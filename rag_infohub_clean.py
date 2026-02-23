import os
import time
import requests
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

# გაფრთხილებების გამორთვა
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# ======================
# 1. GROQ API KEY
# ======================
client = Groq(api_key=os.getenv("groq_api_key"))

# ======================
# 2. ვექტორული ბაზა
# ======================
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(name="infohub")
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# ======================
# 3. საიტის API-დან დოკუმენტების ჩამოტვირთვა
# ======================

def fetch_from_api():
    """infohub.rs.ge-ს API-დან დოკუმენტების ჩამოტვირთვა"""
    documents = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json",
        "Accept-Language": "ka,en;q=0.9",
        "Referer": "https://infohub.rs.ge/ka",
    }

    api_urls = [
        "https://infohub.rs.ge/api/docs?lang=ka&page=1&limit=50",
        "https://infohub.rs.ge/api/docs?lang=ka&page=2&limit=50",
        "https://infohub.rs.ge/api/news?lang=ka&page=1&limit=50",
        "https://infohub.rs.ge/api/faq?lang=ka",
    ]

    for api_url in api_urls:
        try:
            resp = requests.get(api_url, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                items = data if isinstance(data, list) else data.get('data', data.get('items', []))

                for item in items:
                    if isinstance(item, dict):
                        text_parts = [str(item.get(k, '')) for k in ['title', 'content', 'body', 'text', 'description', 'answer', 'question'] if item.get(k)]
                        if text_parts:
                            doc_id = str(item.get('id', ''))
                            documents.append({
                                "text": " ".join(text_parts),
                                "url": f"https://infohub.rs.ge/ka/docs/detail/{doc_id}" if doc_id else api_url,
                                "title": item.get('title', 'დოკუმენტი')
                            })
                print(f"  ✅ {api_url[:60]} — {len(items)} ჩანაწერი")
        except Exception as e:
            print(f"  ⚠️ {api_url[:60]} — {e}")

    return documents


def fetch_direct_docs():
    """კონკრეტული დოკუმენტ ID-ების მიხედვით ჩამოტვირთვა"""
    documents = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json",
    }

    doc_ids = list(range(30920, 30960)) + list(range(1, 30))
    print(f"  📄 ვამოწმებ {len(doc_ids)} დოკუმენტს...")

    for doc_id in doc_ids:
        for endpoint in [f"https://infohub.rs.ge/api/docs/{doc_id}?lang=ka",
                         f"https://infohub.rs.ge/api/document/{doc_id}?lang=ka"]:
            try:
                resp = requests.get(endpoint, headers=headers, timeout=8)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, dict) and data:
                        text_parts = [str(data.get(k, '')) for k in ['title', 'content', 'body', 'text', 'description'] if data.get(k) and len(str(data.get(k))) > 10]
                        if text_parts:
                            documents.append({
                                "text": " ".join(text_parts),
                                "url": f"https://infohub.rs.ge/ka/docs/detail/{doc_id}",
                                "title": data.get('title', f'დოკუმენტი #{doc_id}')
                            })
                            print(f"    ✅ #{doc_id}: {data.get('title', '')[:50]}")
                        break
            except:
                pass
        time.sleep(0.05)

    return documents


def fetch_with_selenium():
    """Selenium-ით ჩამოტვირთვა (JavaScript საიტებისთვის)"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By

        print("  🌐 Selenium გაეშვა...")
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--lang=ka")

        driver = webdriver.Chrome(options=options)
        documents = []

        urls = [
            "https://infohub.rs.ge/ka",
            "https://infohub.rs.ge/ka/docs",
            "https://infohub.rs.ge/ka/news",
            "https://infohub.rs.ge/ka/faq",
        ]

        for url in urls:
            try:
                driver.get(url)
                time.sleep(4)
                text = driver.find_element(By.TAG_NAME, "body").text
                if len(text) > 200:
                    documents.append({"text": text[:6000], "url": url, "title": driver.title})
                    print(f"    ✅ {url} ({len(text)} სიმბოლო)")

                # ბმულების პოვნა და მათი გვერდების ჩატვირთვა
                links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/ka/docs/detail']")
                detail_urls = list(set([l.get_attribute('href') for l in links if l.get_attribute('href')]))[:15]

                for detail_url in detail_urls:
                    try:
                        driver.get(detail_url)
                        time.sleep(3)
                        detail_text = driver.find_element(By.TAG_NAME, "body").text
                        if len(detail_text) > 100:
                            documents.append({"text": detail_text[:6000], "url": detail_url, "title": driver.title})
                            print(f"    ✅ {detail_url[:60]}")
                    except:
                        pass

            except Exception as e:
                print(f"    ⚠️ {url}: {e}")

        driver.quit()
        return documents

    except ImportError:
        print("  ⚠️ Selenium არ არის დაყენებული. გაუშვი: pip install selenium")
        return []
    except Exception as e:
        print(f"  ⚠️ Selenium შეცდომა: {e}")
        return []


# ======================
# 4. ტექსტის დაყოფა
# ======================
def split_text(text, chunk_size=150):
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size) if len(" ".join(words[i:i+chunk_size]).strip()) > 30]


# ======================
# 5. ბაზის შევსება
# ======================
if collection.count() == 0:
    print("🔧 ვავსებ ბაზას...\n")
    all_docs = []

    print("📡 მეთოდი 1: API...")
    all_docs.extend(fetch_from_api())

    if len(all_docs) < 5:
        print("\n📄 მეთოდი 2: პირდაპირი დოკუმენტები...")
        all_docs.extend(fetch_direct_docs())

    if len(all_docs) < 5:
        print("\n🌐 მეთოდი 3: Selenium (ბრაუზერით)...")
        print("  💡 თუ Chrome არ გაქვს: https://chromedriver.chromium.org/downloads")
        all_docs.extend(fetch_with_selenium())

    if all_docs:
        print(f"\n📥 {len(all_docs)} დოკუმენტი ნაპოვნია — ინდექსირება...")
        added = 0
        for doc in all_docs:
            for i, chunk in enumerate(split_text(doc["text"])):
                try:
                    collection.add(
                        documents=[chunk],
                        embeddings=[embedder.encode(chunk).tolist()],
                        ids=[f"{abs(hash(doc['url']))}_{i}"],
                        metadatas=[{"source": doc["url"], "title": doc.get("title", "")}]
                    )
                    added += 1
                except:
                    pass
        print(f"✅ ბაზა შეივსო! ({added} ნაწილი)")
    else:
        print("\n❌ ვერ ჩაიტვირთა ინფორმაცია.")
        print("💡 გამოსავალი: გაუშვი  →  pip install selenium")
        print("   შემდეგ ჩამოტვირთე ChromeDriver: https://chromedriver.chromium.org")
else:
    print(f"✅ ბაზა მზადაა ({collection.count()} ნაწილი)")


# ======================
# 6. კითხვა-პასუხი (RAG)
# ======================
def ask_rag(question):
    count = collection.count()
    if count == 0:
        return "❌ ბაზა ცარიელია. გთხოვთ გადატვირთეთ და Selenium დააყენეთ."

    results = collection.query(
        query_embeddings=[embedder.encode(question).tolist()],
        n_results=min(5, count)
    )

    context = " ".join(results["documents"][0])
    sources = list(set(m["source"] for m in results["metadatas"][0]))

    prompt = f"""შენ ხარ საქართველოს შემოსავლების სამსახურის ექსპერტი ასისტენტი.
ყოველთვის უპასუხე სწორი, გასაგები სალიტერატურო ქართულით.

კონტექსტი:
{context}

კითხვა: {question}

წესები:
- უპასუხე მხოლოდ ქართულად
- გამოიყენე კონტექსტში არსებული ინფორმაცია
- თუ პასუხი კონტექსტში არ არის, თქვი: "ინფორმაცია არ მოიძებნა"
- წერე მკაფიოდ და გასაგებად"""

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    answer = completion.choices[0].message.content
    source_lines = "\n".join(f"  🔗 {s}" for s in sources[:3])

    return f"""{answer}

---
📚 წყარო: საინფორმაციო და მეთოდოლოგიური ჰაბი (საგადასახადო და საბაჟო ადმინისტრირებასთან დაკავშირებული დოკუმენტები)
{source_lines}
🌐 https://infohub.rs.ge/ka"""


# ======================
# 7. CLI ინტერფეისი
# ======================
print("\n🤖 RAG აგენტი მზადაა! (გამოსასვლელად: 'გასვლა')\n")

while True:
    question = input("❓ კითხვა: ").strip()
    if not question:
        continue
    if question.lower() in ["გასვლა", "exit", "quit"]:
        print("👋 ნახვამდის!")
        break

    print("\n🔄 ვეძებ პასუხს...")
    print(f"\n🟢 პასუხი:\n{ask_rag(question)}")
    print("-" * 50 + "\n")

