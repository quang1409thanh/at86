import os
import sys
import json
import argparse
from part1.extractor import process_part1
from common.pdf import extract_images_from_pdf

def main():
    parser = argparse.ArgumentParser(description="TOEIC Content Pipeline")
    parser.add_argument("--part", type=int, required=True, help="TOEIC Part number (1-7)")
    parser.add_argument("--input", type=str, required=True, help="Input file (PDF or Image)")
    parser.add_argument("--output", type=str, help="Output JSON file path")
    parser.add_argument("--id-start", type=int, default=1, help="Starting question ID number")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file {args.input} not found.")
        sys.exit(1)
        
    results = []
    
    input_path = args.input
    output_dir = "temp_media"
    
    if input_path.lower().endswith(".pdf"):
        print(f"[*] PDF detected. Extracting images from {input_path}...")
        image_paths = extract_images_from_pdf(input_path, output_dir)
        if not image_paths:
            print("Error: No images found in PDF.")
            sys.exit(1)
        # For Part 1, we process each extracted image as a separate question
        for i, img_path in enumerate(image_paths):
            results.extend(process_part1(img_path, f"q{args.id_start + i}"))
    else:
        # Assume direct image
        if args.part == 1:
            results = process_part1(input_path, f"q{args.id_start}")
    else:
        print(f"Error: Part {args.part} is not yet implemented.")
        sys.exit(1)
        
    final_output = {
        "part_number": args.part,
        "questions": results
    }
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, indent=4, ensure_ascii=False)
        print(f"[+] Results saved to {args.output}")
    else:
        print(json.dumps(final_output, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    main()
