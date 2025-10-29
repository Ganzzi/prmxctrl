"""
Main code generation tool for prmxctrl SDK.

This script runs the complete code generation pipeline:
1. Fetch and parse schema
2. Generate Pydantic models
3. Generate endpoint classes
4. Generate main client
5. Format and validate generated code

Usage:
    python tools/generate.py
"""

import asyncio
import sys
from pathlib import Path

import jinja2
import typer
from rich.console import Console

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator.analyze_schema import SchemaAnalyzer
from generator.fetch_schema import SchemaFetcher
from generator.generators.client_generator import ClientGenerator
from generator.generators.endpoint_generator import EndpointGenerator
from generator.generators.model_generator import ModelFile, ModelGenerator, PydanticModel
from generator.parse_schema import SchemaParser

app = typer.Typer()
console = Console()


class SDKGenerator:
    """Complete SDK generation pipeline"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.fetcher = SchemaFetcher()
        self.parser = SchemaParser()
        self.analyzer = SchemaAnalyzer()
        self.model_gen = ModelGenerator()
        self.endpoint_gen = EndpointGenerator()
        self.client_gen = ClientGenerator()

    async def generate(self):
        """Run complete generation pipeline"""

        console.print("[bold blue]Starting SDK generation for Proxmox VE 7.4-2[/bold blue]")

        # Step 1: Fetch schema
        console.print("\n[yellow]Step 1:[/yellow] Fetching API schema from GitHub...")
        raw_schema = await self.fetcher.fetch_and_parse()
        console.print(f"[green]✓[/green] Fetched {len(raw_schema)} top-level endpoints")

        # Step 2: Parse schema
        console.print("\n[yellow]Step 2:[/yellow] Parsing schema...")
        endpoints = self.parser.parse(raw_schema)
        console.print("[green]✓[/green] Parsed schema structure")

        # Step 3: Analyze schema
        console.print("\n[yellow]Step 3:[/yellow] Analyzing schema...")
        analysis = self.analyzer.analyze(endpoints)
        console.print(f"[green]✓[/green] Found {analysis.stats.total_endpoints} endpoints")
        console.print(f"[green]✓[/green] Found {analysis.stats.total_methods} methods")

        # Step 4: Generate models
        console.print("\n[yellow]Step 4:[/yellow] Generating Pydantic models...")
        model_name_map = await self._generate_models(endpoints)
        console.print("[green]✓[/green] Generated model files")

        # Step 5: Generate endpoints
        console.print("\n[yellow]Step 5:[/yellow] Generating endpoint classes...")
        await self._generate_endpoints(endpoints, model_name_map)
        console.print("[green]✓[/green] Generated endpoint files")

        # Step 6: Generate main client
        console.print("\n[yellow]Step 6:[/yellow] Generating main client...")
        await self._generate_client(endpoints)
        console.print("[green]✓[/green] Generated ProxmoxClient")

        # Step 7: Format code
        console.print("\n[yellow]Step 7:[/yellow] Formatting generated code...")
        await self._format_code()
        console.print("[green]✓[/green] Formatted with black")

        console.print("\n[bold green]✨ SDK generation complete![/bold green]")

    async def _generate_models(self, endpoints: list):
        """Generate all model files"""
        models_dir = self.output_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)

        # Group endpoints by top-level module
        modules = {}
        for endpoint in endpoints:
            module_name = endpoint.text
            if module_name not in modules:
                modules[module_name] = []

            # Collect all endpoints in this module recursively
            self._collect_endpoints(endpoint, modules[module_name])

        # Generate model file for each module
        model_name_map = {}
        model_files = []
        for module_name, module_endpoints in modules.items():
            code, module_model_names = self.model_gen.generate_models_file_with_names(
                module_endpoints, module_name
            )
            model_name_map.update(module_model_names)

            output_file = models_dir / f"{module_name}.py"
            output_file.write_text(code)

            # Create ModelFile for __init__.py generation
            # Parse the models from the code (simplified)
            models = []
            for line in code.split("\n"):
                if line.startswith("class ") and "(BaseModel):" in line:
                    model_name = line.split("class ")[1].split("(BaseModel):")[0].strip()
                    models.append(PydanticModel(name=model_name, fields=[]))
            model_files.append(ModelFile(filename=f"{module_name}.py", models=models, imports=[]))

        # Generate __init__.py with proper exports
        self.model_gen._write_init_file(models_dir, model_files)

        return model_name_map

    async def _generate_endpoints(self, endpoints: list, model_name_map: dict):
        """Generate all endpoint files"""
        endpoints_dir = self.output_dir / "endpoints"
        endpoints_dir.mkdir(parents=True, exist_ok=True)

        # Use the new multi-pass endpoint generation
        endpoint_files = self.endpoint_gen.generate_endpoints(endpoints, model_name_map)

        # Write each endpoint file
        for endpoint_file in endpoint_files:
            file_path = endpoints_dir / endpoint_file.file_path
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Generate code for this file
            code = self._generate_endpoint_file_code(endpoint_file)
            file_path.write_text(code)

        # Generate __init__.py
        init_file = endpoints_dir / "__init__.py"
        init_code = '"""Generated endpoint classes"""\n'
        init_file.write_text(init_code)

    def _generate_endpoint_file_code(self, endpoint_file) -> str:
        """Generate code for a single endpoint file"""
        # Set up Jinja2 environment
        template_dir = Path(__file__).parent.parent / "generator" / "templates"
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        template = env.get_template("endpoint.py.jinja")

        # Update imports
        imports = self._collect_imports(endpoint_file.classes)
        endpoint_file.imports = imports

        # Render template
        content = template.render(
            classes=endpoint_file.classes,
            imports=endpoint_file.imports,
        )

        return content

    def _collect_imports(self, classes):
        """Collect imports needed for endpoint classes"""
        imports = []
        seen_imports = set()

        # Map model prefixes to modules
        model_module_map = {
            "Access": "access",
            "Cluster": "cluster",
            "Nodes": "nodes",
            "Pools": "pools",
            "Storage": "storage",
            "Version": "version",
        }

        for cls in classes:
            # Collect imports from properties
            for prop in cls.properties:
                import_path = prop.get("import_path")
                if import_path and import_path not in seen_imports:
                    imports.append(f"from {import_path} import {prop['class']}")
                    seen_imports.add(import_path)

            # Collect imports from call method
            if cls.call_method:
                import_path = cls.call_method.get("import_path")
                class_name = cls.call_method.get("item_class")
                if import_path and class_name and import_path not in seen_imports:
                    imports.append(f"from {import_path} import {class_name}")
                    seen_imports.add(import_path)

            # Collect imports from method parameters and return types
            for method in cls.methods:
                # Import parameter model
                param_model = method.get("param_model")
                if param_model:
                    module = self._get_model_module(param_model, model_module_map)
                    import_stmt = f"from prmxctrl.models.{module} import {param_model}"
                    if import_stmt not in seen_imports:
                        imports.append(import_stmt)
                        seen_imports.add(import_stmt)

                # Import response model
                response_model = method.get("response_model")
                if response_model:
                    module = self._get_model_module(response_model, model_module_map)
                    import_stmt = f"from prmxctrl.models.{module} import {response_model}"
                    if import_stmt not in seen_imports:
                        imports.append(import_stmt)
                        seen_imports.add(import_stmt)

        return "\n".join(imports)

    def _get_model_module(self, model_name, module_map):
        """Determine the module for a model name"""
        # Extract prefix from model name (e.g., "NodesGETRequest" -> "Nodes")
        for prefix, module in module_map.items():
            if model_name.startswith(prefix):
                return module
        # Default fallback
        return "nodes"

    async def _generate_client(self, endpoints: list):
        """Generate main client file"""
        code = self.client_gen.generate(endpoints)

        output_file = self.output_dir / "client.py"
        output_file.write_text(code)

        # Also update __init__.py
        init_file = self.output_dir / "__init__.py"
        init_code = '''"""
Proxmox VE Python SDK
Auto-generated type-safe client for Proxmox VE API v7.4-2
"""

from prmxctrl.client import ProxmoxClient

__version__ = "0.1.1"
__all__ = ["ProxmoxClient"]
'''
        init_file.write_text(init_code)

    async def _format_code(self):
        """Format generated code with black"""
        import subprocess

        try:
            subprocess.run(["black", str(self.output_dir)], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            console.print(f"[yellow]Warning: black formatting failed: {e}[/yellow]")
        except FileNotFoundError:
            console.print("[yellow]Warning: black not found, skipping formatting[/yellow]")

    def _collect_endpoints(self, endpoint, collection: list):
        """Recursively collect all endpoints"""
        collection.append(endpoint)
        for child in endpoint.children:
            self._collect_endpoints(child, collection)


@app.command()
def generate(
    output_dir: Path = typer.Option(
        Path("prmxctrl"), "--output", "-o", help="Output directory for generated SDK"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force regeneration even if output exists"
    ),
):
    """Generate Proxmox VE SDK from API schema"""

    if output_dir.exists() and not force:
        console.print(f"[red]Error:[/red] Output directory {output_dir} already exists")
        console.print("Use --force to regenerate")
        raise typer.Exit(1)

    generator = SDKGenerator(output_dir)
    asyncio.run(generator.generate())


if __name__ == "__main__":
    app()
