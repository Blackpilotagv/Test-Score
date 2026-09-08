import os
import sys
from datetime import timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal, Base, engine
from app.models.models import User, UserRole, UserStatus, Exam, ExamStatus, Test, TestStatus, Question, QuestionSet, QuestionSetStatus
from app.core.security import get_password_hash
from app.services.scheduler_service import get_current_ist_date, get_ist_12pm_utc

def seed_db():
    print("Re-creating database tables for updated schema...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    current_ist = get_current_ist_date()
    today_str = current_ist.strftime("%Y-%m-%d")
    tomorrow_str = (current_ist + timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        # 1. Seed Users
        admin_user = User(
            name="TNPSC Administrator",
            email="admin@tnpsc.com",
            mobile="9876543210",
            password_hash=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE
        )
        db.add(admin_user)

        student_user = User(
            name="Raja Guru",
            email="student@tnpsc.com",
            mobile="9876543211",
            password_hash=get_password_hash("student123"),
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE
        )
        db.add(student_user)
        db.commit()
        print("Seeded Admin & Student users.")

        # 2. Seed Exams (Strictly 3 categories: Group 1, Group 2, Group 4)
        exam_data = [
            {
                "name": "TNPSC Group 1",
                "slug": "tnpsc-group-1",
                "description": "Deputy Collector, DSP & Class-I Services Daily Mock Assessments (Tamil Medium).",
                "price": 99.0,
                "language_mode": "TA",
                "status": ExamStatus.ACTIVE
            },
            {
                "name": "TNPSC Group 2",
                "slug": "tnpsc-group-2",
                "description": "Sub Registrar, Municipal Commissioner & Group 2 Services (Tamil + English Medium).",
                "price": 49.0,
                "language_mode": "TA_EN",
                "status": ExamStatus.ACTIVE
            },
            {
                "name": "TNPSC Group 4",
                "slug": "tnpsc-group-4",
                "description": "VAO, Junior Assistant, Typist & Steno-Typist Examinations (Tamil Medium).",
                "price": 29.0,
                "status": ExamStatus.ACTIVE
            }
        ]

        exams_by_slug = {}
        for edata in exam_data:
            e = Exam(**edata)
            db.add(e)
            db.commit()
            db.refresh(e)
            exams_by_slug[edata["slug"]] = e
            print(f"Seeded Exam: {e.name} (Language Mode: {e.language_mode})")

        # 3. Seed Group 4 Daily Assessment #24 (Tamil Only)
        group4_exam = exams_by_slug["tnpsc-group-4"]
        test_g4 = Test(
            exam_id=group4_exam.id,
            title="Daily Assessment #24",
            description="Comprehensive Daily Mock Assessment covering Tamil Literature, Indian Polity & History.",
            test_date=today_str,
            duration_minutes=30,
            question_count=5,
            price=29.0,
            status=TestStatus.PUBLISHED
        )
        db.add(test_g4)
        db.commit()
        db.refresh(test_g4)

        # Create QuestionSet for Today (ACTIVE)
        qs_g4_today = QuestionSet(
            exam_id=group4_exam.id,
            test_id=test_g4.id,
            title=f"Group 4 Daily Test - {today_str}",
            schedule_date=today_str,
            publish_at=get_ist_12pm_utc(current_ist),
            expire_at=get_ist_12pm_utc(current_ist + timedelta(days=1)),
            status=QuestionSetStatus.ACTIVE,
            question_count=5,
            created_by=admin_user.id
        )
        db.add(qs_g4_today)

        # Create QuestionSet for Tomorrow (SCHEDULED)
        qs_g4_tomorrow = QuestionSet(
            exam_id=group4_exam.id,
            test_id=test_g4.id,
            title=f"Group 4 Daily Test - {tomorrow_str}",
            schedule_date=tomorrow_str,
            publish_at=get_ist_12pm_utc(current_ist + timedelta(days=1)),
            expire_at=get_ist_12pm_utc(current_ist + timedelta(days=2)),
            status=QuestionSetStatus.SCHEDULED,
            question_count=5,
            created_by=admin_user.id
        )
        db.add(qs_g4_tomorrow)
        db.commit()
        db.refresh(qs_g4_today)
        db.refresh(qs_g4_tomorrow)

        g4_questions_ta = [
            {
                "question_group_id": 401,
                "language": "ta",
                "question_text": "திராவிட சங்கத்தை மெட்ராஸில் (1912) நிறுவியவர் யார்?",
                "option_a": "சி. நடேச முதலியார்",
                "option_b": "டி.எம். நாயர்",
                "option_c": "பி. தியாகராய செட்டி",
                "option_d": "ஈ.வெ. இராமசாமி",
                "correct_option": "A",
                "explanation": "1912 இல் டாக்டர் சி. நடேச முதலியார் மெட்ராஸ் திராவிட சங்கத்தை தொடங்கினார்.",
                "question_order": 1
            },
            {
                "question_group_id": 402,
                "language": "ta",
                "question_text": "தமிழ்நாட்டின் மாநில மரம் எது?",
                "option_a": "ஆலமரம்",
                "option_b": "பனை மரம்",
                "option_c": "தென்னை மரம்",
                "option_d": "வேப்ப மரம்",
                "correct_option": "B",
                "explanation": "பனை மரம் தமிழ்நாட்டின் அதிகாரப்பூர்வ மாநில மரமாகும்.",
                "question_order": 2
            },
            {
                "question_group_id": 403,
                "language": "ta",
                "question_text": "திருக்குறளில் உள்ள மொத்த அதிகாரங்களின் எண்ணிக்கை எவ்வளவு?",
                "option_a": "100",
                "option_b": "133",
                "option_c": "150",
                "option_d": "1000",
                "correct_option": "B",
                "explanation": "திருக்குறள் 133 அதிகாரங்களையும் 1330 குறட்பாக்களையும் கொண்டுள்ளது.",
                "question_order": 3
            },
            {
                "question_group_id": 404,
                "language": "ta",
                "question_text": "இந்திய அரசியலமைப்பின் எந்த வித விதி 'தீண்டாமை ஒழிப்பு' பற்றி கூறுகிறது?",
                "option_a": "விதி 14",
                "option_b": "விதி 17",
                "option_c": "விதி 19",
                "option_d": "விதி 21",
                "correct_option": "B",
                "explanation": "அரசியலமைப்பு விதி 17 தீண்டாமை ஒழிப்பை உறுதி செய்கிறது.",
                "question_order": 4
            },
            {
                "question_group_id": 405,
                "language": "ta",
                "question_text": "கீழடி அகழ்வாராய்ச்சி தமிழ்நாட்டின் எந்த மாவட்டத்தில் அமைந்துள்ளது?",
                "option_a": "மதுரை",
                "option_b": "சிவகங்கை",
                "option_c": "தேனி",
                "option_d": "திண்டுக்கல்",
                "correct_option": "B",
                "explanation": "கீழடி பழங்கால சங்ககால அகழ்வாராய்ச்சி தளம் சிவகங்கை மாவட்டத்தில் அமைந்துள்ளது.",
                "question_order": 5
            }
        ]

        for qdata in g4_questions_ta:
            db.add(Question(test_id=test_g4.id, question_set_id=qs_g4_today.id, source="MANUAL", status="ACTIVE", **qdata))
            db.add(Question(test_id=test_g4.id, question_set_id=qs_g4_tomorrow.id, source="MANUAL", status="ACTIVE", **qdata))

        db.commit()
        print("Seeded Group 4 Questions for Today's ACTIVE set and Tomorrow's SCHEDULED set.")

        # 4. Seed Group 2 Daily Assessment #08 (Dual Language: Tamil + English)
        group2_exam = exams_by_slug["tnpsc-group-2"]
        test_g2 = Test(
            exam_id=group2_exam.id,
            title="Daily Assessment #08",
            description="Bilingual Mock Assessment covering Indian Economy & Science (Tamil & English Dual Mode).",
            test_date=today_str,
            duration_minutes=45,
            question_count=3,
            price=49.0,
            status=TestStatus.PUBLISHED
        )
        db.add(test_g2)
        db.commit()
        db.refresh(test_g2)

        qs_g2_today = QuestionSet(
            exam_id=group2_exam.id,
            test_id=test_g2.id,
            title=f"Group 2 Dual Daily Set - {today_str}",
            schedule_date=today_str,
            publish_at=get_ist_12pm_utc(current_ist),
            expire_at=get_ist_12pm_utc(current_ist + timedelta(days=1)),
            status=QuestionSetStatus.ACTIVE,
            question_count=3,
            created_by=admin_user.id
        )
        db.add(qs_g2_today)

        qs_g2_tomorrow = QuestionSet(
            exam_id=group2_exam.id,
            test_id=test_g2.id,
            title=f"Group 2 Dual Daily Set - {tomorrow_str}",
            schedule_date=tomorrow_str,
            publish_at=get_ist_12pm_utc(current_ist + timedelta(days=1)),
            expire_at=get_ist_12pm_utc(current_ist + timedelta(days=2)),
            status=QuestionSetStatus.SCHEDULED,
            question_count=3,
            created_by=admin_user.id
        )
        db.add(qs_g2_tomorrow)
        db.commit()
        db.refresh(qs_g2_today)
        db.refresh(qs_g2_tomorrow)

        g2_questions_dual = [
            # Question 1 (Pair: Tamil & English share question_group_id=201)
            {
                "question_group_id": 201,
                "language": "ta",
                "question_text": "இந்திய ரிசர்வ் வங்கி (RBI) எந்த ஆண்டில் தொடங்கப்பட்டது?",
                "option_a": "1935",
                "option_b": "1947",
                "option_c": "1950",
                "option_d": "1921",
                "correct_option": "A",
                "explanation": "இந்திய ரிசர்வ் வங்கி ஏப்ரல் 1, 1935 இல் தொடங்கப்பட்டது.",
                "question_order": 1
            },
            {
                "question_group_id": 201,
                "language": "en",
                "question_text": "In which year was the Reserve Bank of India (RBI) established?",
                "option_a": "1935",
                "option_b": "1947",
                "option_c": "1950",
                "option_d": "1921",
                "correct_option": "A",
                "explanation": "The Reserve Bank of India was established on April 1, 1935 under the Reserve Bank of India Act.",
                "question_order": 1
            },
            # Question 2 (Pair: Tamil & English share question_group_id=202)
            {
                "question_group_id": 202,
                "language": "ta",
                "question_text": "ஒளிச்சேர்க்கையின் போது தாவரங்களால் வெளியிடப்படும் வாயு எது?",
                "option_a": "காரபன் டை ஆக்சைடு",
                "option_b": "ஆக்ஸிஜன்",
                "option_c": "நைட்ரஜன்",
                "option_d": "ஹைட்ரஜன்",
                "correct_option": "B",
                "explanation": "ஒளிச்சேர்க்கையின் போது தாவரங்கள் ஆக்ஸிஜனை வெளியிடுகின்றன.",
                "question_order": 2
            },
            {
                "question_group_id": 202,
                "language": "en",
                "question_text": "Which gas is released by plants during photosynthesis?",
                "option_a": "Carbon Dioxide",
                "option_b": "Oxygen",
                "option_c": "Nitrogen",
                "option_d": "Hydrogen",
                "correct_option": "B",
                "explanation": "Plants release Oxygen gas as a byproduct during photosynthesis.",
                "question_order": 2
            },
            # Question 3 (Pair: Tamil & English share question_group_id=203)
            {
                "question_group_id": 203,
                "language": "ta",
                "question_text": "ஜிஎஸ்டி (GST) இந்தியாவில் எப்போது அமல்படுத்தப்பட்டது?",
                "option_a": "ஜூலை 1, 2017",
                "option_b": "நவம்பர் 8, 2016",
                "option_c": "ஜனவரி 1, 2018",
                "option_d": "ஏப்ரல் 1, 2015",
                "correct_option": "A",
                "explanation": "சரக்கு மற்றும் சேவை வரி (GST) ஜூலை 1, 2017 முதல் அமலுக்கு வந்தது.",
                "question_order": 3
            },
            {
                "question_group_id": 203,
                "language": "en",
                "question_text": "When was GST implemented in India?",
                "option_a": "July 1, 2017",
                "option_b": "November 8, 2016",
                "option_c": "January 1, 2018",
                "option_d": "April 1, 2015",
                "correct_option": "A",
                "explanation": "Goods and Services Tax (GST) came into effect in India on July 1, 2017.",
                "question_order": 3
            }
        ]

        for qdata in g2_questions_dual:
            db.add(Question(test_id=test_g2.id, question_set_id=qs_g2_today.id, source="MANUAL", status="ACTIVE", **qdata))
            db.add(Question(test_id=test_g2.id, question_set_id=qs_g2_tomorrow.id, source="MANUAL", status="ACTIVE", **qdata))

        db.commit()
        print("Seeded Group 2 Dual Language Question Sets (Tamil & English paired).")

        # 5. Seed Group 1 Daily Assessment #12 (Tamil Only)
        group1_exam = exams_by_slug["tnpsc-group-1"]
        test_g1 = Test(
            exam_id=group1_exam.id,
            title="Daily Assessment #12",
            description="Premier Civil Services Daily Assessment on Polity & Governance.",
            test_date=today_str,
            duration_minutes=30,
            question_count=2,
            price=99.0,
            status=TestStatus.PUBLISHED
        )
        db.add(test_g1)
        db.commit()
        db.refresh(test_g1)

        qs_g1_today = QuestionSet(
            exam_id=group1_exam.id,
            test_id=test_g1.id,
            title=f"Group 1 Daily Set - {today_str}",
            schedule_date=today_str,
            publish_at=get_ist_12pm_utc(current_ist),
            expire_at=get_ist_12pm_utc(current_ist + timedelta(days=1)),
            status=QuestionSetStatus.ACTIVE,
            question_count=2,
            created_by=admin_user.id
        )
        db.add(qs_g1_today)

        qs_g1_tomorrow = QuestionSet(
            exam_id=group1_exam.id,
            test_id=test_g1.id,
            title=f"Group 1 Daily Set - {tomorrow_str}",
            schedule_date=tomorrow_str,
            publish_at=get_ist_12pm_utc(current_ist + timedelta(days=1)),
            expire_at=get_ist_12pm_utc(current_ist + timedelta(days=2)),
            status=QuestionSetStatus.SCHEDULED,
            question_count=2,
            created_by=admin_user.id
        )
        db.add(qs_g1_tomorrow)
        db.commit()
        db.refresh(qs_g1_today)
        db.refresh(qs_g1_tomorrow)

        g1_questions_ta = [
            {
                "question_group_id": 101,
                "language": "ta",
                "question_text": "நிதி ஆயோக்கின் அடல் இன்னோவேஷன் மிஷனின் (AIM) முதன்மை நோக்கம் என்ன?",
                "option_a": "வேளாண் மானிய விரிவாக்கம்",
                "option_b": "புதுமை மற்றும் தொழில்முனைவோரை ஊக்குவித்தல்",
                "option_c": "அந்நிய நேரடி முதலீட்டு வசதி",
                "option_d": "டிஜிட்டல் வங்கி உள்கட்டமைப்பு",
                "correct_option": "B",
                "explanation": "அடல் இன்னோவேஷன் மிஷன் என்பது இந்தியாவில் புதுமை மற்றும் தொழில்முனைவோரை ஊக்குவிப்பதற்கான நிதி ஆயோக்கின் முதன்மை திட்டமாகும்.",
                "question_order": 1
            },
            {
                "question_group_id": 102,
                "language": "ta",
                "question_text": "இந்திய அரசியலமைப்பின் தந்தை என்று அழைக்கப்படுபவர் யார்?",
                "option_a": "டாக்டர் பி.ஆர். அம்பேத்கர்",
                "option_b": "மகாத்மா காந்தி",
                "option_c": "ஜவஹர்லால் நேரு",
                "option_d": "சர்தார் பட்டேல்",
                "correct_option": "A",
                "explanation": "டாக்டர் பி.ஆர். அம்பேத்கர் இந்திய அரசியலமைப்பின் முதன்மை வரைவாளர் மற்றும் தந்தை என அறியப்படுகிறார்.",
                "question_order": 2
            }
        ]

        for qdata in g1_questions_ta:
            db.add(Question(test_id=test_g1.id, question_set_id=qs_g1_today.id, source="MANUAL", status="ACTIVE", **qdata))
            db.add(Question(test_id=test_g1.id, question_set_id=qs_g1_tomorrow.id, source="MANUAL", status="ACTIVE", **qdata))

        db.commit()
        print("Seeded Group 1 Question Sets for Today's ACTIVE set and Tomorrow's SCHEDULED set.")

        # Seed Past Year Question Papers (2025-2021)
        from app.models.models import PastYearPaper, PastYearPaperStatus

        years = [2025, 2024, 2023, 2022, 2021]
        for y in years:
            # Group 4 Past Paper
            p_g4 = PastYearPaper(
                exam_id=group4_exam.id,
                year=y,
                title=f"TNPSC Group 4 Original Paper {y}",
                description=f"Official TNPSC Group 4 General Studies & Tamil Language Question Paper ({y}).",
                duration_minutes=180,
                question_count=200,
                marks_per_question=1.5,
                negative_mark=0.0,
                price=0.0,
                status=PastYearPaperStatus.PUBLISHED,
                created_by=admin_user.id
            )
            db.add(p_g4)
            db.commit()
            db.refresh(p_g4)

            # Sample question for G4
            db.add(Question(
                past_year_paper_id=p_g4.id,
                question_group_id=5000 + y,
                language="ta",
                question_text=f"TNPSC Group 4 ({y}) மாதிரி கேள்வி: திருக்குறளில் உள்ள அதிகாரங்களின் எண்ணிக்கை எத்தனை?",
                option_a="133",
                option_b="108",
                option_c="120",
                option_d="150",
                correct_option="A",
                explanation="திருக்குறள் 133 அதிகாரங்களையும் 1330 குறட்பாக்களையும் கொண்டுள்ளது.",
                question_order=1,
                source="MANUAL",
                question_source="ORIGINAL"
            ))

            # Group 2 Past Paper (Dual language)
            p_g2 = PastYearPaper(
                exam_id=group2_exam.id,
                year=y,
                title=f"TNPSC Group 2 & 2A Preliminary Original Paper {y}",
                description=f"Official TNPSC Group 2 Preliminary Examination Question Paper in Tamil & English ({y}).",
                duration_minutes=180,
                question_count=200,
                marks_per_question=1.5,
                negative_mark=0.0,
                price=0.0 if y != 2025 else 49.0,  # 2025 paper premium, others free
                status=PastYearPaperStatus.PUBLISHED,
                created_by=admin_user.id
            )
            db.add(p_g2)
            db.commit()
            db.refresh(p_g2)

            grp_id_g2 = 6000 + y
            db.add(Question(
                past_year_paper_id=p_g2.id,
                question_group_id=grp_id_g2,
                language="ta",
                question_text=f"TNPSC Group 2 ({y}): இந்திய அரசியலமைப்பு சாசனம் ஏற்றுக்கொள்ளப்பட்ட நாள் எது?",
                option_a="நவம்பர் 26, 1949",
                option_b="ஜனவரி 26, 1950",
                option_c="ஆகஸ்ட் 15, 1947",
                option_d="ஜனவரி 30, 1948",
                correct_option="A",
                explanation="இந்திய அரசியலமைப்பு சாசனம் 1949 நவம்பர் 26 அன்று ஏற்றுக்கொள்ளப்பட்டது.",
                question_order=1,
                source="MANUAL",
                question_source="ORIGINAL"
            ))
            db.add(Question(
                past_year_paper_id=p_g2.id,
                question_group_id=grp_id_g2,
                language="en",
                question_text=f"TNPSC Group 2 ({y}): When was the Constitution of India adopted by the Constituent Assembly?",
                option_a="November 26, 1949",
                option_b="January 26, 1950",
                option_c="August 15, 1947",
                option_d="January 30, 1948",
                correct_option="A",
                explanation="The Constitution of India was adopted on 26 November 1949 and came into effect on 26 January 1950.",
                question_order=1,
                source="MANUAL",
                question_source="ORIGINAL"
            ))

            # Group 1 Past Paper
            p_g1 = PastYearPaper(
                exam_id=group1_exam.id,
                year=y,
                title=f"TNPSC Group 1 Prelims Question Paper {y}",
                description=f"Official TNPSC Group 1 General Studies Preliminary Question Paper ({y}).",
                duration_minutes=180,
                question_count=200,
                marks_per_question=1.5,
                negative_mark=0.0,
                price=0.0,
                status=PastYearPaperStatus.PUBLISHED,
                created_by=admin_user.id
            )
            db.add(p_g1)
            db.commit()
            db.refresh(p_g1)

            db.add(Question(
                past_year_paper_id=p_g1.id,
                question_group_id=7000 + y,
                language="ta",
                question_text=f"TNPSC Group 1 ({y}): தென்னிந்தியாவின் கங்கை என்று அழைக்கப்படும் ஆறு எது?",
                option_a="காவிரி",
                option_b="கோதாவரி",
                option_c="கிருஷ்ணா",
                option_d="வைகை",
                correct_option="B",
                explanation="கோதாவரி ஆறு தென்னிந்தியாவின் கங்கை (தட்சிண கங்கா) என்று அழைக்கப்படுகிறது.",
                question_order=1,
                source="MANUAL",
                question_source="ORIGINAL"
            ))

        db.commit()
        print("Seeded Past Year Papers (2025-2021) for Group 1, Group 2, and Group 4.")

        print("Database re-seeding completed successfully with QuestionSets, PastYearPapers, and zero Group 4A entries!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
