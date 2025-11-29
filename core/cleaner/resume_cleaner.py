
import re

class ResumeCleaner:
    def clean(self, text):
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'<.*?>', '', text)
        return text.strip()
