import streamlit as st
import google.generativeai as genai
import zipfile
import io

st.set_page_config(page_title="Mr Sky Shark V03", page_icon="🦈", layout="wide")
st.title("🦈 Mr Sky Shark V03 - Advanced SRT Engine")

# --- تهيئة الذاكرة الدائمة ---
if "zip_data" not in st.session_state:
    st.session_state.zip_data = None

# --- الإعدادات الجانبية ---
st.sidebar.header("⚙️ الإعدادات (Settings)")
provider = st.sidebar.selectbox("اختر محرك الترجمة:", ["Gemini (Google)"])
api_key = st.sidebar.text_input("مفتاح الـ API:", type="password")
model_choice = st.sidebar.text_input("اسم النموذج:", value="gemini-1.5-pro")

# قاموس المصطلحات والبرومبت
st.sidebar.subheader("📖 قاموس المصطلحات (Glossary)")
glossary_input = st.sidebar.text_area("أمثلة: Crown Prince: ولي العهد", height=150)

default_prompt = """You are an expert subtitle translator. Translate to eloquent Arabic.
Strictly maintain SRT structure (Index, Timecode, Text). 
Do not add conversational filler.
CRITICAL: 1-to-1 mapping. Do not merge or omit lines."""

st.subheader("📝 تخصيص البرومبت (Prompt Customization)")
custom_prompt = st.text_area("البرومبت الموجه للذكاء الاصطناعي:", value=default_prompt, height=150)

# --- الدوال البرمجية ---
def get_full_instruction(custom_prompt, glossary_text):
    glossary = {}
    for line in glossary_text.split('\n'):
        if ':' in line:
            parts = line.split(':', 1)
            glossary[parts[0].strip()] = parts[1].strip()
    
    full_prompt = custom_prompt
    if glossary:
        full_prompt += "\n\nUSE THESE GLOSSARY TERMS (MANDATORY):\n"
        for term, translation in glossary.items():
            full_prompt += f"- {term} -> {translation}\n"
    return full_prompt

def split_srt_into_blocks(srt_content, blocks_per_chunk):
    normalized = srt_content.replace("\r\n", "\n").strip()
    raw_blocks = normalized.split("\n\n")
    blocks = [b.strip() for b in raw_blocks if b.strip()]
    chunks = []
    for i in range(0, len(blocks), blocks_per_chunk):
        chunks.append("\n\n".join(blocks[i:i + blocks_per_chunk]))
    return chunks

# --- واجهة العمل ---
uploaded_files = st.file_uploader("ارفع ملفات الترجمة (.srt)", type=["srt"], accept_multiple_files=True)
batch_size = st.number_input("حجم الدفعة (عدد الكتل):", min_value=5, max_value=100, value=25)

if uploaded_files and st.button("🚀 ابدأ الترجمة الشاملة"):
    if not api_key:
        st.error("⚠️ يرجى إدخال مفتاح الـ API.")
    else:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=model_choice)
        
        final_system_instruction = get_full_instruction(custom_prompt, glossary_input)
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for file in uploaded_files:
                st.write(f"### 🔄 جاري معالجة: {file.name}")
                srt_content = file.read().decode("utf-8", errors="ignore")
                chunks = split_srt_into_blocks(srt_content, batch_size)
                
                translated_blocks = []
                progress_bar = st.progress(0)
                
                for idx, chunk in enumerate(chunks):
                    full_prompt = f"{final_system_instruction}\n\nTranslate this SRT chunk:\n{chunk}"
                    try:
                        response = model.generate_content(full_prompt)
                        translated_blocks.append(response.text.strip())
                    except Exception as e:
                        st.error(f"خطأ في {file.name}: {e}")
                        translated_blocks.append(chunk) 
                    
                    progress_bar.progress((idx + 1) / len(chunks))
                
                final_srt_content = "\n\n".join(translated_blocks)
                zf.writestr(f"Translated_{file.name}", final_srt_content)
                st.success(f"✅ تم الانتهاء من {file.name}")

        # حفظ النتيجة في الذاكرة الدائمة
        st.session_state.zip_data = zip_buffer.getvalue()
        st.balloons()

# --- زر التحميل الدائم ---
if st.session_state.zip_data is not None:
    st.download_button(
        label="📥 تحميل الملفات المترجمة (ZIP)",
        data=st.session_state.zip_data,
        file_name="Translated_Subtitles.zip",
        mime="application/zip"
    )
    if st.button("🔄 مسح النتائج للبدء من جديد"):
        st.session_state.zip_data = None
        st.rerun()
