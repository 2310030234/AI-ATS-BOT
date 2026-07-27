import os
import pdfplumber

JD_FOLDER = "uploads/jd"
RESUME_FOLDER = "uploads/resumes"


def extract_pdf(path):
    text = ""

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"

    return text


def get_jd():

    files = os.listdir(JD_FOLDER)

    if not files:
        return None

    return extract_pdf(os.path.join(JD_FOLDER, files[0]))


def get_resumes():

    resumes = []

    for file in os.listdir(RESUME_FOLDER):

        if file.endswith(".pdf"):

            txt = extract_pdf(os.path.join(RESUME_FOLDER, file))

            resumes.append((file, txt))

    return resumes