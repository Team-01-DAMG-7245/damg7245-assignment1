# robust_layout_detector.py
# Version-compatible layout detection that handles API differences

import os
import cv2
import json
import argparse
import numpy as np
from pathlib import Path
from PIL import Image
import pdfplumber
import layoutparser as lp
import torch


def load_robust_lp_model(model_dir="publaynet-model"):
    """
    Load LayoutParser model with version compatibility handling
    """
    print(f"Loading local Detectron2 model from: {model_dir}")
    
    model_path = Path(model_dir)
    
    config_files = list(model_path.glob("*.yaml")) + list(model_path.glob("*.yml"))
    weight_files = list(model_path.glob("*.pth"))
    
    config_files = list(dict.fromkeys(config_files))
    weight_files = list(dict.fromkeys(weight_files))
    
    print(f"Found config files: {[f.name for f in config_files]}")
    print(f"Found weight files: {[f.name for f in weight_files]}")
    
    if not config_files or not weight_files:
        print("❌ ERROR: Missing config or weight files")
        return None
    
    config_path = config_files[0]
    weight_path = weight_files[0]
    
    print(f"Using config: {config_path}")
    print(f"Using weights: {weight_path}")
    
    # Try different loading approaches for compatibility
    model = None
    
    # Approach 1: Standard LayoutParser loading
    try:
        print("🔄 Trying standard LayoutParser loading...")
        model = lp.Detectron2LayoutModel(
            config_path=str(config_path),
            model_path=str(weight_path),
            extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.3],
            label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
        )
        print("✅ Standard loading successful")
        return model
    except Exception as e:
        print(f"❌ Standard loading failed: {e}")
    
    # Approach 2: Minimal config loading
    try:
        print("🔄 Trying minimal config loading...")
        model = lp.Detectron2LayoutModel(
            config_path=str(config_path),
            model_path=str(weight_path),
            label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
        )
        print("✅ Minimal loading successful")
        return model
    except Exception as e:
        print(f"❌ Minimal loading failed: {e}")
    
    # Approach 3: Direct Detectron2 loading (fallback)
    try:
        print("🔄 Trying direct Detectron2 loading...")
        model = DirectDetectron2Model(config_path, weight_path)
        print("✅ Direct Detectron2 loading successful")
        return model
    except Exception as e:
        print(f"❌ Direct loading failed: {e}")
    
    print("❌ All loading approaches failed")
    return None


class DirectDetectron2Model:
    """
    Direct Detectron2 model wrapper when LayoutParser fails
    """
    def __init__(self, config_path, weight_path):
        from detectron2.engine import DefaultPredictor
        from detectron2.config import get_cfg
        from detectron2 import model_zoo
        
        self.cfg = get_cfg()
        
        # Try to load config
        try:
            self.cfg.merge_from_file(str(config_path))
        except:
            # Fallback to a standard config
            self.cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml"))
        
        self.cfg.MODEL.WEIGHTS = str(weight_path)
        self.cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.3
        self.cfg.MODEL.ROI_HEADS.NUM_CLASSES = 5
        
        self.predictor = DefaultPredictor(self.cfg)
        
        # Label mapping
        self.label_map = {0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}
    
    def detect(self, image):
        """Detect layout blocks in image"""
        outputs = self.predictor(image)
        
        instances = outputs["instances"].to("cpu")
        
        # Convert to LayoutParser-style blocks
        blocks = []
        
        if len(instances) > 0:
            boxes = instances.pred_boxes.tensor.numpy()
            classes = instances.pred_classes.numpy()
            scores = instances.scores.numpy()
            
            for i, (box, cls, score) in enumerate(zip(boxes, classes, scores)):
                x1, y1, x2, y2 = box
                
                # Create a simple block object
                block = SimpleBlock(
                    coordinates=(x1, y1, x2, y2),
                    type=self.label_map.get(cls, f"Class_{cls}"),
                    score=score
                )
                blocks.append(block)
        
        return blocks


class SimpleBlock:
    """Simple block object compatible with LayoutParser interface"""
    def __init__(self, coordinates, type, score):
        self.coordinates = coordinates
        self.type = type
        self.score = score


def robust_detect_layout(model, opencv_image):
    """
    Robust detection that handles different model types
    """
    try:
        # Standard LayoutParser detection
        if hasattr(model, 'detect'):
            return model.detect(opencv_image)
        
        # Direct Detectron2 model
        elif hasattr(model, 'predictor'):
            return model.detect(opencv_image)
        
        else:
            raise Exception("Unknown model type")
            
    except Exception as e:
        print(f"Detection failed: {e}")
        return []


def save_safe_visualization(opencv_image, layout, output_path):
    """
    Create visualization that's guaranteed to work
    """
    try:
        # Make a copy of the image
        viz_image = opencv_image.copy()
        
        # Colors for different types
        colors = {
            'Text': (0, 255, 0),      # Green
            'Title': (255, 0, 0),     # Blue  
            'List': (0, 255, 255),    # Yellow
            'Table': (255, 0, 255),   # Magenta
            'Figure': (0, 128, 255)   # Orange
        }
        
        for block in layout:
            x1, y1, x2, y2 = map(int, block.coordinates)
            color = colors.get(block.type, (128, 128, 128))
            
            # Draw rectangle
            cv2.rectangle(viz_image, (x1, y1), (x2, y2), color, 2)
            
            # Add text label
            label = f"{block.type} ({block.score:.2f})"
            text_y = max(y1 - 10, 15)
            cv2.putText(viz_image, label, (x1, text_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        success = cv2.imwrite(str(output_path), viz_image)
        return success
        
    except Exception as e:
        print(f"Visualization failed: {e}")
        return False


def extract_layout_robust(pdf_path, output_base_dir="data/parsed", model_dir="publaynet-model", save_viz=True):
    """
    Robust layout extraction that handles version compatibility issues
    """
    pdf_path = Path(pdf_path)
    output_base_dir = Path(output_base_dir)

    layout_dir = output_base_dir / "layout" / pdf_path.stem
    layout_dir.mkdir(parents=True, exist_ok=True)

    # Load model with robust approach
    model = load_robust_lp_model(model_dir)
    if model is None:
        print("❌ Failed to load any model variant")
        return None

    layout_results = []

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"\nProcessing {total_pages} pages from {pdf_path.name}")

        for page_num, page in enumerate(pdf.pages, 1):
            print(f"Processing page {page_num}/{total_pages}", end=" ")

            try:
                # Convert page to image
                img = page.to_image(resolution=200)
                pil_image = img.original
                opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

                # Robust detection
                layout = robust_detect_layout(model, opencv_image)
                
                print(f"({len(layout)} detections)", end=" ")

                # Process blocks
                page_blocks = []
                for idx, block in enumerate(layout):
                    x1, y1, x2, y2 = block.coordinates
                    
                    page_blocks.append({
                        "block_id": idx,
                        "type": str(block.type),
                        "confidence": float(block.score),
                        "bbox": {"x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2)},
                        "width": float(x2 - x1),
                        "height": float(y2 - y1),
                    })

                # Count by type
                block_counts = {}
                for b in page_blocks:
                    block_type = b["type"]
                    block_counts[block_type] = block_counts.get(block_type, 0) + 1

                # Save page data
                page_layout = {
                    "pdf_name": pdf_path.name,
                    "page_number": page_num,
                    "total_blocks": len(page_blocks),
                    "blocks": page_blocks,
                    "block_types": block_counts,
                    "model_used": type(model).__name__
                }
                layout_results.append(page_layout)

                # Save JSON
                page_layout_file = layout_dir / f"page_{page_num:03d}_layout.json"
                with open(page_layout_file, "w") as f:
                    json.dump(page_layout, f, indent=2)

                # Save visualization
                if page_blocks and save_viz:
                    viz_file = layout_dir / f"page_{page_num:03d}_layout_viz.png"
                    save_safe_visualization(opencv_image, layout, viz_file)

                print(f"- blocks: {dict(block_counts)}")

            except Exception as e:
                print(f"- Error: {e}")
                continue

    # Save summary
    total_blocks = sum(p["total_blocks"] for p in layout_results)
    all_types = set()
    for p in layout_results:
        all_types.update(p["block_types"].keys())
    
    overall_block_counts = {t: 0 for t in all_types}
    for p in layout_results:
        for t, c in p["block_types"].items():
            overall_block_counts[t] = overall_block_counts.get(t, 0) + c

    summary = {
        "pdf_name": pdf_path.name,
        "total_pages": len(layout_results),
        "total_blocks": total_blocks,
        "overall_block_counts": overall_block_counts,
        "model_used": type(model).__name__,
        "pages": layout_results,
    }

    summary_file = layout_dir / "layout_summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n✅ Layout analysis complete!")
    print(f"Results saved to: {layout_dir}")
    print(f"Total blocks detected: {total_blocks}")
    print(f"Block distribution: {overall_block_counts}")

    return summary


def process_all_pdfs_robust(raw_dir="data/raw", parsed_dir="data/parsed", model_dir="publaynet-model", save_viz=True):
    """Process all PDFs with robust detection"""
    raw_path = Path(raw_dir)
    pdf_files = list(raw_path.rglob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {raw_path}")
        return

    print(f"Found {len(pdf_files)} PDF files to process:")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file}")

    for pdf_file in pdf_files:
        try:
            print(f"\n{'='*60}")
            print(f"Processing: {pdf_file.name}")
            print(f"{'='*60}")
            extract_layout_robust(pdf_file, parsed_dir, model_dir, save_viz)
        except Exception as e:
            print(f"Error processing {pdf_file}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Robust layout detection with version compatibility")
    parser.add_argument("--pdf", help="Path to specific PDF file")
    parser.add_argument("--raw-dir", default="data/raw", help="Directory containing raw PDFs")
    parser.add_argument("--parsed-dir", default="data/parsed", help="Base directory for parsed outputs")
    parser.add_argument("--model-dir", default="publaynet-model", help="Directory containing model files")
    parser.add_argument("--no-viz", action="store_true", help="Skip visualization")
    args = parser.parse_args()

    save_viz = not args.no_viz

    if args.pdf:
        extract_layout_robust(args.pdf, args.parsed_dir, args.model_dir, save_viz)
    else:
        process_all_pdfs_robust(args.raw_dir, args.parsed_dir, args.model_dir, save_viz)