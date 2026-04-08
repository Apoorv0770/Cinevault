import PyPDF2
import sys

def read_pdf(filename):
    try:
        reader = PyPDF2.PdfReader(filename)
        text = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text.append(t)
        
        with open('pdf_content.txt', 'w', encoding='utf-8') as f:
            f.write('\n\n---PAGE---\n\n'.join(text))
        print("Successfully wrote to pdf_content.txt")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    read_pdf('new.pdf')
