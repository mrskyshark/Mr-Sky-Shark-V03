import streamlit as st
import google.generativeai as genai
import zipfile
import io
import time

st.set_page_config(page_title="Mr Sky Shark V03", page_icon="🦈", layout="wide")
st.title("🦈 Mr Sky Shark V03 - Advanced SRT Engine")

# --- الإعدادات الجانبية ---
st.sidebar.header("⚙️ الإعدادات (Settings)")

# اختيار المحرك (الهيكل جاهز للتوسيع)
provider = st.sidebar.selectbox("اختر محرك الترجمة:", ["Gemini (Google)", "Claude (Anthropic) - قريباً", "GPT (OpenAI) - قريباً"])
api_key = st.sidebar.text_input("مفتاح الـ API:", type="password")
model_choice = st.sidebar.text_input("اسم النموذج:", value="gemini-1.5-pro")

# قاموس المصطلحات (Glossary)
st.sidebar.subheader("📖 قاموس المصطلحات (Glossary)")
st.sidebar.info("اكتب المصطلح الإنجليزي ثم نقطتين ثم الترجمة. مثال:\nCrown Prince: ولي العهد")
glossary_input = st.sidebar.text_area("أدخل المصطلحات هنا:", height=150)

# إعدادات التقسيم
batch_size = st.sidebar.number_input("حجم الدفعة (عدد الكتل):", min_value=5, max_value=100, value=25)

# --- الدوال البرمجية ---

def parse_glossary(text):
    glossary = {}
    for line in text.split('\n'):
        if ':' in line:
            parts = line.split(':', 1)
            glossary[parts[0].strip()] = parts[1].strip()
    return glossary

def get_system_instruction(glossary_text):
    base_prompt = """You are an expert subtitle translator. Translate to eloquent Arabic.
    Strictly maintain SRT structure (Index, Timecode, Text). 
    Do not add conversational filler.
    CRITICAL: 1-to-1 mapping. Do not merge or omit lines.
    """
    glossary = parse_glossary(glossary_text)
    if glossary:
        base_prompt += "\n\nUSE THESE GLOSSARY TERMS (MANDATORY):\n"
        for term, translation in glossary.items():
            base_prompt += f"- {term} -> {translation}\n"
    return base_prompt

def split_srt_into_blocks(srt_content, blocks_per_chunk):
    normalized = srt_content.replace("\r\n", "\n").strip()
    raw_blocks = normalized.split("\n\n")
    blocks = [b.strip() for b in raw_blocks if b.strip()]
    chunks = []
    for i in range(0, len(blocks), blocks_per_chunk):
        chunks.append("\n\n".join(blocks[i:i + blocks_per_chunk]))
    return chunks

# --- واجهة رفع الملفات ---
uploaded_files = st.file_uploader("ارفع ملفات الترجمة (.srt)", type=["srt"], accept_multiple_files=True)

if uploaded_files and st.button("🚀 ابدأ الترجمة الشاملة"):
    if not api_key:
        st.error("⚠️ يرجى إدخال مفتاح الـ API.")
    else:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=model_choice)
        
        # حاوية لتخزين النتائج
        final_results = {}
        
        # ملف ZIP للتحميل النهائي
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            
            for file in uploaded_files:
                st.write(f"### 🔄 جاري معالجة: {file.name}")
                srt_content = file.read().decode("utf-8", errors="ignore")
                chunks = split_srt_into_blocks(srt_content, batch_size)
                
                translated_blocks = []
                progress_bar = st.progress(0)
                
                # المعالجة
                system_instr = get_system_instruction(glossary_input)
                
                for idx, chunk in enumerate(chunks):
                    # دمج البرومبت مع الكتلة
                    full_prompt = f"{system_instr}\n\nTranslate this SRT chunk:\n{chunk}"
                    
                    try:
                        response = model.generate_content(full_prompt)
                        translated_blocks.append(response.text.strip())
                    except Exception as e:
                        st.error(f"خطأ في {file.name}: {e}")
                        translated_blocks.append(chunk) # في حال الخطأ نضع الأصلي لتفادي الكراش
                    
                    progress_bar.progress((idx + 1) / len(chunks))
                
                # تجميع الملف
                final_srt_content = "\n\n".join(translated_blocks)
                zf.writestr(f"Translated_{file.name}", final_srt_content)
                st.success(f"✅ تم الانتهاء من {file.name}")

        # زر التحميل النهائي
        zip_buffer.seek(0)
        st.download_button(
            label="📥 تحميل جميع الملفات (ZIP)",
            data=zip_buffer,
            file_name="Translated_Subtitles.zip",
            mime="application/zip"
        )
        st.balloons()