"""
Test script for PDF Parser
"""

from src.doc_parser import DocumentParser

# Initialize parser
parser = DocumentParser()

# Use the absolute path to your PDF
text, metadata = parser.parse("data/raw/sop_sample_parse.pdf")


print('='*60)
print('EXTRACTED TEXT (first 500 chars)')
print('='*60)
print(text[:500])
print('\n' + '='*60)
print('METADATA')
print('='*60)
for key, value in metadata.items():
    print(f'{key}: {value}')



