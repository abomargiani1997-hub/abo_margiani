# abo_margiani
# RAG აგენტი infohub.rs.ge-სთვის

ეს პროექტი წარმოადგენს RAG (Retrieval-Augmented Generation) აგენტს,
რომელიც იღებს ინფორმაციას [infohub.rs.ge](https://infohub.rs.ge/ka)-ზე 
განთავსებული საგადასახადო და საბაჟო დოკუმენტებიდან და პასუხობს 
კითხვებს ქართულად.

## გამოყენებული ტექნოლოგიები

- Python 3.10+
- Groq API (LLM)
- ChromaDB (ვექტორული ბაზა)
- Sentence-Transformers (ემბედინგები)
- Selenium (საიტის კითხვა)
- Requests + BeautifulSoup

## გაშვება

1. დააყენე ბიბლიოთეკები:
```bash
pip install groq python-dotenv chromadb sentence-transformers selenium requests beautifulsoup4
```

2. შექმენი `.env` ფაილი:
```
GROQ_API_KEY=შენი_API_KEY
```

3. გაუშვი:
```bash
python rag_infohub_clean.py
```

## წყარო

საინფორმაციო და მეთოდოლოგიური ჰაბი — საგადასახადო და საბაჟო 
ადმინისტრირებასთან დაკავშირებული დოკუმენტები და ინფორმაცია ერთ სივრცეში.

🔗 https://infohub.rs.ge/ka
