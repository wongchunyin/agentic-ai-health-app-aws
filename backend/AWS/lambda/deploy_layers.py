import os
import zipfile
import json
from pathlib import Path
import sys
# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from AWS.shared.utils import ArgumentParser
from AWS.shared.config import Config


def deploy_weather_utils_layer(layer_name: str, desc: str):
    # Paths
    print(f"Deploying layer: {layer_name}")
    layer_source = Config.get_lambda_layer_path(layer_name)
    zip_path = Config.get_lambda_layer_zip_path(layer_name)
    print(f"Layer source: {layer_source}")
    print(f"Zip path: {zip_path}")

    # Check if layer directory exists
    if not layer_source.exists():
        raise FileNotFoundError(f"Layer directory not found: {layer_source}")

    # Install dependencies if requirements.txt exists
    requirements_file = layer_source / "requirements.txt"
    python_dir = layer_source / "python"
    
    if requirements_file.exists():
        print("Installing dependencies...")
        import subprocess
        subprocess.run([
            "pip", "install", "-r", str(requirements_file), 
            "-t", str(python_dir)
        ], check=True)

    # Create zip
    files_added = 0
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add all python files and packages
        if python_dir.exists():
            for file_path in python_dir.rglob("*"):
                if file_path.is_file():
                    arcname = f"python/{file_path.relative_to(python_dir)}"
                    zipf.write(file_path, arcname)
                    files_added += 1
    
    if files_added == 0:
        raise ValueError(f"No files found to add to layer zip for {layer_name}")
    
    print(f"Created zip with {files_added} files")
    
    # Deploy to Lambda
    lambda_client = Config.get_client('lambda', region_name=Config.LAMBDA_REGION)
    
    with open(zip_path, 'rb') as f:
        zip_content = f.read()
        
    response = lambda_client.publish_layer_version(
        LayerName=f"{layer_name.replace('_', '-')}-layer",
        Description=desc or "Bug fix and features upgrade",
        Content={'ZipFile': zip_content},
        CompatibleRuntimes=['python3.8', 'python3.9', 'python3.10', 'python3.11', 'python3.12'],
        LicenseInfo='MIT'
    )
    
    layer_version_arn = response['LayerVersionArn']
    print(f"Published layer version: {layer_version_arn}")

    # if the deployment is successful, remove the zip file to save space
    if os.path.exists(zip_path):
        os.remove(zip_path)
        print(f"Removed temporary zip file: {zip_path}")
        
    return layer_version_arn

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('--layer_name', type=str, help="Name of the Lambda layer")
    parser.add_argument('--desc', help="The description of version")
    args = parser.parse_args()

    
    if args.layer_name: 
        deploy_weather_utils_layer(layer_name=args.layer_name, desc=args.desc)
    else:
        raise ValueError("Layer name must be provided via --layer_name argument.")