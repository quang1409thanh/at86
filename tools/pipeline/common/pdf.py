import fitz # PyMuPDF
import os

def extract_images_from_pdf(pdf_path: str, output_dir: str):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    doc = fitz.open(pdf_path)
    extracted_paths = []
    
    for page_index in range(len(doc)):
        page = doc[page_index]
        image_list = page.get_images(full=True)
        
        # In Part 1, we usually expect 1 main photo per page
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            ext = base_image["ext"]
            
            image_filename = f"part1_p{page_index+1}_i{img_index+1}.{ext}"
            image_path = os.path.join(output_dir, image_filename)
            
            with open(image_path, "wb") as f:
                f.write(image_bytes)
            
            extracted_paths.append(image_path)
            
    doc.close()
    return extracted_paths
