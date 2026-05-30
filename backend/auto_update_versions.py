#!/usr/bin/env python3
"""
Script to automatically get latest layer versions from AWS and update SAM templates
"""
import os
import re
import boto3
import json

# Layer name mappings
LAYER_MAPPINGS = {
    'ToolkitLayerVersion': 'toolkit-layer',
    'GeminiLayerVersion': 'gemini-layer', 
    'AWSLayerVersion': 'aws-layer',
    'MessageLayerVersion': 'message-layer',
    'LivewellCoreLayerVersion': 'livewell-core-layer',
    'AIAgentLayerVersion': 'ai-agent-layer'
}

def get_latest_layer_versions():
    """Get latest version numbers for all layers from AWS"""
    session = boto3.Session(profile_name='account2')
    lambda_client = session.client('lambda', region_name='us-east-1')
    
    versions = {}
    
    for param_name, layer_name in LAYER_MAPPINGS.items():
        try:
            response = lambda_client.list_layer_versions(LayerName=layer_name)
            if response['LayerVersions']:
                latest_version = response['LayerVersions'][0]['Version']
                versions[param_name] = latest_version
                print(f"✅ {layer_name}: {latest_version}")
            else:
                print(f"❌ No versions found for {layer_name}")
        except Exception as e:
            print(f"❌ Error getting {layer_name}: {e}")
    
    return versions

def update_sam_template(file_path, versions):
    """Update layer versions in a SAM template"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    updated = False
    for param_name, version in versions.items():
        pattern = f'({param_name}:.*?Default:\\s*)(\\d+)'
        if re.search(pattern, content, flags=re.DOTALL):
            content = re.sub(pattern, f'\\g<1>{version}', content, flags=re.DOTALL)
            updated = True
    
    if updated:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Updated {file_path}")
    else:
        print(f"⏭️  No updates needed for {file_path}")

def find_sam_templates():
    """Find all SAM templates"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    functions_dir = os.path.join(script_dir, 'AWS/lambda/functions')
    sam_files = []
    
    for root, dirs, files in os.walk(functions_dir):
        for file in files:
            if file == 'sam.yaml':
                sam_files.append(os.path.join(root, file))
    
    return sam_files

def main():
    print("🚀 Getting latest layer versions from AWS...")
    
    versions = get_latest_layer_versions()
    
    if not versions:
        print("❌ No layer versions found")
        return
    
    print(f"\n📝 Updating SAM templates...")
    sam_files = find_sam_templates()
    
    for sam_file in sam_files:
        try:
            update_sam_template(sam_file, versions)
        except Exception as e:
            print(f"❌ Error updating {sam_file}: {e}")
    
    print(f"\n✅ Processed {len(sam_files)} SAM templates")

if __name__ == "__main__":
    main()