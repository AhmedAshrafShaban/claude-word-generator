import streamlit as st
import io
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
# استدعاء دالة التوليد من ملفك القديم
from ai import generate

# دالة مخصصة للويب: تحفظ الوورد في الذاكرة بدلاً من الهارد ديسك
def create_word_buffer(data):
    doc = Document()
    title = doc.add_heading(data["title"], 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    if data.get("subtitle"):
        subtitle = doc.add_paragraph(data["subtitle"])
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
    for chapter in data["chapters"]:
        ch_title = doc.add_heading(chapter["title"], level=1)
        ch_title.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        for block_type, content in chapter["blocks"]:
            if block_type == "h2":
                h2 = doc.add_heading(content, level=2)
                h2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            elif block_type == "p":
                p = doc.add_paragraph(content)
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                for run in p.runs:
                    run.font.size = Pt(12)
    
    # حفظ الملف في الذاكرة ليتم تحميله عبر المتصفح
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# ----------------- تصميم واجهة الموقع -----------------
st.set_page_config(page_title="مولد الكتيبات الذكي", page_icon="📚")

st.title("📚 مولد الكتيبات الذكي")
st.write("أدخل فكرتك هنا وسنقوم بتوليد كتيب كامل ومنسق كملف Word.")

# مدخلات المستخدم
idea = st.text_input("عن ماذا تريد أن تكتب؟", placeholder="مثال: أهمية القراءة السريعة")
tone = st.selectbox("اختر نبرة الكتابة:", ["simple", "academic", "literary", "journalistic"])

# زر التشغيل
if st.button("توليد الكتيب"):
    if not idea.strip():
        st.warning("رجاءً أدخل فكرة أولاً!")
    else:
        # شريط تحميل يظهر للمستخدم
        with st.spinner("جاري الكتابة والتنسيق... (نحن الآن في الوضع التجريبي)"):
            def st_progress(percent, msg):
                pass # يمكن تطويرها لاحقاً لربطها بشريط التقدم في واجهة الويب
            
            # استدعاء الذكاء الاصطناعي
            result, usage = generate(idea, tone, st_progress)
            
            # تحويل النتيجة لملف وورد
            word_buffer = create_word_buffer(result)
            
            st.success("تم إنشاء الكتيب بنجاح! 🎉")
            
            # زر التحميل المباشر
            st.download_button(
                label="📥 تحميل ملف الوورد",
                data=word_buffer,
                file_name=f"{result['title']}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )