import json
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
# بنستدعي دالة الذكاء الاصطناعي اللي عملناها في الملف التاني
from ai import generate

def create_word_document(data, filename="my_book.docx"):
    print("\nجاري إنشاء ملف الـ Word وتنسيقه...")
    doc = Document()
    
    # إضافة العنوان الرئيسي
    title = doc.add_heading(data["title"], 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # إضافة العنوان الفرعي (إن وجد)
    if data.get("subtitle"):
        subtitle = doc.add_paragraph(data["subtitle"])
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
    # إضافة الفصول
    for chapter in data["chapters"]:
        # عنوان الفصل
        ch_title = doc.add_heading(chapter["title"], level=1)
        ch_title.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        
        # محتوى الفصل (عناوين فرعية وفقرات)
        for block_type, content in chapter["blocks"]:
            if block_type == "h2":
                h2 = doc.add_heading(content, level=2)
                h2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            elif block_type == "p":
                p = doc.add_paragraph(content)
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                # تظبيط الخط عشان يكون واضح للغة العربية
                for run in p.runs:
                    run.font.size = Pt(12)

    # حفظ الملف
    doc.save(filename)
    print(f"تم حفظ الملف بنجاح! هتلاقيه جنبك باسم: {filename}")

if __name__ == "__main__":
    # دالة بسيطة لطباعة نسبة الإنجاز
    def my_progress(percent, msg):
        print(f"[{percent}%] {msg}")

    # هنا بتكتب الفكرة اللي عايز الكتاب أو الكتيب عنها
    idea = "أهمية القراءة السريعة وكيفية تطبيقها"
    
    print("بسم الله.. بدأنا:")
    # 1. تشغيل دالة التوليد (من ملف ai.py)
    result, usage = generate(idea, "simple", my_progress)
    
    # 2. إرسال النتيجة لدالة الوورد لإنشاء الملف
    create_word_document(result, "كتاب_القراءة_السريعة.docx")