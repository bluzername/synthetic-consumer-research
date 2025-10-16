"""File management utilities for output organization."""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import shutil


class FileManager:
    """Manage file I/O and output directory structure."""
    
    def __init__(self, base_output_dir: str = "outputs"):
        """
        Initialize file manager.
        
        Args:
            base_output_dir: Base directory for all outputs
        """
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(exist_ok=True)
    
    def create_output_directory(self, product_name: str) -> Path:
        """
        Create timestamped output directory for a product concept.
        
        Args:
            product_name: Name of the product
        
        Returns:
            Path to created directory
        """
        # Clean product name for filesystem
        clean_name = self._sanitize_filename(product_name)
        
        # Create timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create directory name
        dir_name = f"{clean_name}_{timestamp}"
        output_dir = self.base_output_dir / dir_name
        
        # Create directory structure
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "images").mkdir(exist_ok=True)
        (output_dir / "posts").mkdir(exist_ok=True)
        (output_dir / "analytics").mkdir(exist_ok=True)
        
        return output_dir
    
    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize filename by removing invalid characters.
        
        Args:
            name: Original name
        
        Returns:
            Sanitized filename
        """
        # Replace spaces with underscores
        name = name.replace(" ", "_")
        
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, "")
        
        # Limit length
        max_length = 50
        if len(name) > max_length:
            name = name[:max_length]
        
        return name.lower()
    
    def save_json(self, data: Dict[str, Any], filepath: Path):
        """
        Save data as JSON file.
        
        Args:
            data: Data to save
            filepath: Path to save file
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def save_text(self, content: str, filepath: Path):
        """
        Save text content to file.
        
        Args:
            content: Text content
            filepath: Path to save file
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def save_image(self, image_data: bytes, filepath: Path):
        """
        Save image data to file.
        
        Args:
            image_data: Image bytes
            filepath: Path to save file
        """
        with open(filepath, 'wb') as f:
            f.write(image_data)
    
    def load_json(self, filepath: Path) -> Dict[str, Any]:
        """
        Load JSON file.
        
        Args:
            filepath: Path to JSON file
        
        Returns:
            Loaded data
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_text(self, filepath: Path) -> str:
        """
        Load text file.
        
        Args:
            filepath: Path to text file
        
        Returns:
            File content
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    def list_outputs(self) -> List[str]:
        """
        List all output directories.
        
        Returns:
            List of output directory names
        """
        if not self.base_output_dir.exists():
            return []
        
        return [
            d.name for d in self.base_output_dir.iterdir()
            if d.is_dir()
        ]
    
    def get_latest_output(self) -> Path:
        """
        Get path to most recent output directory.
        
        Returns:
            Path to latest output
        """
        outputs = list(self.base_output_dir.iterdir())
        if not outputs:
            raise FileNotFoundError("No output directories found")
        
        # Sort by modification time
        latest = max(outputs, key=lambda p: p.stat().st_mtime)
        return latest
    
    def copy_file(self, src: Path, dest: Path):
        """Copy file from src to dest."""
        shutil.copy2(src, dest)
    
    def ensure_dir(self, path: Path):
        """Ensure directory exists."""
        path.mkdir(parents=True, exist_ok=True)

