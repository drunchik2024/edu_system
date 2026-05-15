"""
Скрипт заполнения БД тестовыми данными.
Запуск: python seed.py
Данные полностью пересоздаются при каждом запуске.
"""
import asyncio
from app.auth import hash_password
from app.database import AsyncSessionLocal, engine, Base
from app.models import (
    Role, Department, User, EducationalProgram, Discipline,
    ChecklistCategory, ChecklistItem, ReportStatus,
    Competency, ProgramCompetency, ProgramDisciplineItem,
)
from app.models.report_file import ReportFile
from app.models.program import ProgramLevel, EducationFormEnum
from app.models.report import ReportStatusEnum
from app.models.rop import CompetencyType


async def seed():
    # Пересоздаём схему с нуля
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:

        # ── Роли ──────────────────────────────────────────────────────────────
        role_head     = Role(name="head_of_department",  display_name="Заведующий кафедрой")
        role_director = Role(name="program_director",    display_name="Руководитель ОП")
        role_teacher  = Role(name="teacher",             display_name="Преподаватель")
        role_dean     = Role(name="dean",                display_name="Декан")
        db.add_all([role_head, role_director, role_teacher, role_dean])
        await db.flush()

        # ── Кафедры ───────────────────────────────────────────────────────────
        dept_cs      = Department(name="Кафедра информатики и вычислительной техники", code="ИВТ")
        dept_math    = Department(name="Кафедра высшей математики",                     code="ВМ")
        dept_physics = Department(name="Кафедра физики",                                code="ФИЗ")
        dept_econ    = Department(name="Кафедра экономики и менеджмента",               code="ЭМ")
        db.add_all([dept_cs, dept_math, dept_physics, dept_econ])
        await db.flush()

        # ── Пользователи ──────────────────────────────────────────────────────
        def user(full_name, email, role, dept):
            return User(
                full_name=full_name,
                email=email,
                hashed_password=hash_password("password123"),
                role_id=role.id,
                department_id=dept.id,
            )

        head      = user("Смирнов Андрей Викторович",    "head@vgtu.ru",        role_head,     dept_cs)
        # rop — демо-аккаунт руководителя ОП с готовыми программами
        rop_user  = user("Козлова Ирина Петровна",       "rop@vgtu.ru",         role_director, dept_cs)
        dir1      = user("Козлова Ирина Петровна",       "director1@vgtu.ru",   role_director, dept_cs)
        dir2      = user("Новиков Сергей Александрович", "director2@vgtu.ru",   role_director, dept_cs)
        dir3      = user("Фёдорова Елена Дмитриевна",    "director3@vgtu.ru",   role_director, dept_cs)
        dir4      = user("Белов Игорь Николаевич",       "director4@vgtu.ru",   role_director, dept_cs)
        dir5      = user("Громова Ольга Павловна",       "director5@vgtu.ru",   role_director, dept_cs)
        t1        = user("Петров Михаил Юрьевич",        "teacher1@vgtu.ru",    role_teacher,  dept_cs)
        t2        = user("Иванова Наталья Сергеевна",    "teacher2@vgtu.ru",    role_teacher,  dept_cs)
        t3        = user("Захаров Дмитрий Олегович",     "teacher3@vgtu.ru",    role_teacher,  dept_math)
        t4        = user("Соколова Анна Васильевна",     "teacher4@vgtu.ru",    role_teacher,  dept_math)
        t5        = user("Орлов Павел Игоревич",         "teacher5@vgtu.ru",    role_teacher,  dept_cs)
        t6        = user("Крылова Марина Владимировна",  "teacher6@vgtu.ru",    role_teacher,  dept_cs)
        t7        = user("Волков Алексей Тимурович",     "teacher7@vgtu.ru",    role_teacher,  dept_physics)
        t8        = user("Ершова Светлана Борисовна",    "teacher8@vgtu.ru",    role_teacher,  dept_econ)
        db.add_all([head, rop_user, dir1, dir2, dir3, dir4, dir5, t1, t2, t3, t4, t5, t6, t7, t8])
        await db.flush()

        # ── Образовательные программы (10 штук) ──────────────────────────────
        def prog(name, code, level, year, director, dept, desc=""):
            return EducationalProgram(
                name=name, code=code, level=level, start_year=year,
                director_id=director.id, department_id=dept.id, description=desc,
            )

        p1 = prog(
            "Информатика и вычислительная техника", "09.03.01",
            ProgramLevel.bachelor, 2022, dir1, dept_cs,
            "Программа готовит специалистов в области разработки ПО, системного анализа и "
            "проектирования информационных систем. Выпускники владеют современными технологиями "
            "web-разработки, баз данных и машинного обучения.",
        )
        p2 = prog(
            "Прикладная математика и информатика", "01.03.02",
            ProgramLevel.bachelor, 2021, dir2, dept_cs,
            "Программа ориентирована на подготовку специалистов с глубокими знаниями "
            "математических методов и их применения в информационных технологиях.",
        )
        p3 = prog(
            "Информационные системы и технологии", "09.04.02",
            ProgramLevel.master, 2023, dir1, dept_cs,
            "Магистерская программа для подготовки специалистов высокой квалификации "
            "в области проектирования и внедрения корпоративных ИС.",
        )
        p4 = prog(
            "Программная инженерия", "09.03.04",
            ProgramLevel.bachelor, 2022, dir3, dept_cs,
            "Программа готовит инженеров-программистов, способных проектировать "
            "и сопровождать крупные программные комплексы.",
        )
        p5 = prog(
            "Кибербезопасность", "10.03.01",
            ProgramLevel.bachelor, 2023, dir4, dept_cs,
            "Программа направлена на подготовку специалистов по защите информации, "
            "анализу угроз и обеспечению информационной безопасности.",
        )
        p6 = prog(
            "Интеллектуальные системы управления", "09.04.01",
            ProgramLevel.master, 2022, dir3, dept_cs,
            "Магистерская программа по разработке систем искусственного интеллекта "
            "и интеллектуальных систем управления.",
        )
        p7 = prog(
            "Прикладная информатика", "09.03.03",
            ProgramLevel.bachelor, 2021, dir5, dept_cs,
            "Программа готовит специалистов по созданию прикладных ИС, "
            "автоматизации бизнес-процессов и аналитике данных.",
        )
        p8 = prog(
            "Технологии разработки программного обеспечения", "09.05.01",
            ProgramLevel.specialist, 2020, dir2, dept_cs,
            "Специалитет по комплексной подготовке разработчиков ПО "
            "для оборонной и критической инфраструктуры.",
        )
        p9 = prog(
            "Математическое обеспечение и администрирование ИС", "02.03.03",
            ProgramLevel.bachelor, 2022, dir4, dept_cs,
            "Программа ориентирована на разработку алгоритмического и математического "
            "обеспечения информационных систем.",
        )
        p10 = prog(
            "Большие данные и машинное обучение", "09.04.03",
            ProgramLevel.master, 2024, dir5, dept_cs,
            "Магистерская программа по технологиям обработки больших данных, "
            "глубокому обучению и аналитике.",
        )
        db.add_all([p1, p2, p3, p4, p5, p6, p7, p8, p9, p10])
        await db.flush()

        # ── Дисциплины кафедры ИВТ (24 штуки) ───────────────────────────────
        def disc(name, code, program, t_primary, t_secondary, goals="", objectives="", outcomes=""):
            return Discipline(
                name=name, code=code,
                program_id=program.id, department_id=dept_cs.id,
                teacher_primary_id=t_primary.id,
                teacher_secondary_id=t_secondary.id,
                goals=goals, objectives=objectives, outcomes=outcomes,
            )

        cs_disciplines = [
            disc("Базы данных", "Б1.О.14", p1, t1, t2,
                 "Сформировать навыки проектирования реляционных БД.",
                 "Теория реляционных БД, SQL, проектирование схем, оптимизация запросов.",
                 "Умение проектировать БД, писать SQL-запросы, работать с PostgreSQL."),
            disc("Алгоритмы и структуры данных", "Б1.О.09", p1, t2, t1,
                 "Освоить классические алгоритмы и структуры данных.",
                 "Анализ сложности, реализация структур, сортировки и поиск.",
                 "Способность выбирать оптимальные алгоритмы для задач."),
            disc("Разработка веб-приложений", "Б1.В.03", p1, t1, t5,
                 "Подготовить к разработке современных веб-приложений.",
                 "HTML/CSS, JavaScript, фреймворки, REST API, развёртывание.",
                 "Умение самостоятельно разрабатывать полноценные веб-приложения."),
            disc("Операционные системы", "Б1.О.11", p1, t5, t6,
                 "Изучить принципы работы ОС и системного программирования.",
                 "Процессы, потоки, память, файловые системы, Linux.",
                 "Умение администрировать ОС и писать системные программы."),
            disc("Компьютерные сети", "Б1.О.12", p1, t6, t5,
                 "Изучить архитектуру и протоколы компьютерных сетей.",
                 "Модель OSI/TCP-IP, маршрутизация, DNS, HTTP, безопасность сетей.",
                 "Умение проектировать сети и администрировать сетевое оборудование."),
            disc("Объектно-ориентированное программирование", "Б1.О.07", p1, t1, t2,
                 "Освоить парадигму ООП и её реализацию на Java/C++.",
                 "Классы, наследование, полиморфизм, паттерны проектирования.",
                 "Умение проектировать программы с применением ООП."),

            disc("Машинное обучение", "Б1.В.08", p2, t2, t1,
                 "Изучить методы МО и их применение на практике.",
                 "Классификация, регрессия, кластеризация, нейросети, Python.",
                 "Способность применять алгоритмы МО для прикладных задач."),
            disc("Математическая статистика и теория вероятностей", "Б1.О.05", p2, t5, t6,
                 "Изучить основы теории вероятностей и математической статистики.",
                 "Случайные величины, законы распределения, выборочный метод.",
                 "Умение применять статистические методы для анализа данных."),
            disc("Численные методы", "Б1.О.06", p2, t6, t5,
                 "Освоить численные методы решения математических задач.",
                 "Решение СЛАУ, нелинейных уравнений, интерполяция, интегрирование.",
                 "Умение реализовывать численные методы в программном коде."),
            disc("Анализ данных и визуализация", "Б1.В.05", p2, t2, t5,
                 "Изучить технологии анализа и визуализации данных.",
                 "Pandas, NumPy, Matplotlib, Power BI, дашборды.",
                 "Умение проводить исследовательский анализ данных."),

            disc("Проектирование информационных систем", "М1.О.02", p3, t1, t2,
                 "Освоить методологии проектирования корпоративных ИС.",
                 "UML, архитектурные паттерны, микросервисы, документирование.",
                 "Умение проектировать сложные ИС корпоративного уровня."),
            disc("Облачные вычисления и DevOps", "М1.В.03", p3, t5, t6,
                 "Изучить технологии облачных вычислений и DevOps-практики.",
                 "Docker, Kubernetes, CI/CD, AWS/Azure, мониторинг.",
                 "Умение разворачивать приложения в облачной инфраструктуре."),
            disc("Корпоративные базы данных", "М1.О.04", p3, t1, t5,
                 "Изучить архитектуру корпоративных СУБД.",
                 "Oracle, PostgreSQL, репликация, секционирование, NoSQL.",
                 "Умение администрировать и оптимизировать корпоративные СУБД."),

            disc("Программирование на Python", "Б1.О.08", p4, t2, t6,
                 "Освоить язык Python для разработки приложений.",
                 "Синтаксис, ООП, библиотеки, тестирование, async.",
                 "Умение разрабатывать полноценные приложения на Python."),
            disc("Архитектура программных систем", "Б1.В.04", p4, t1, t2,
                 "Изучить современные архитектурные подходы к разработке ПО.",
                 "Монолит, микросервисы, событийная архитектура, DDD.",
                 "Умение выбирать и обосновывать архитектурные решения."),
            disc("Тестирование программного обеспечения", "Б1.В.06", p4, t5, t1,
                 "Освоить методологии и инструменты тестирования ПО.",
                 "Unit, интеграционное, E2E тестирование, TDD, Selenium.",
                 "Умение разрабатывать и выполнять планы тестирования."),

            disc("Криптография и защита информации", "Б1.О.09", p5, t6, t5,
                 "Изучить основы криптографии и методы защиты информации.",
                 "Симметричная/асимметричная криптография, PKI, TLS, ЭЦП.",
                 "Умение применять криптографические средства защиты."),
            disc("Безопасность веб-приложений", "Б1.В.04", p5, t2, t6,
                 "Изучить уязвимости веб-приложений и методы защиты.",
                 "OWASP Top 10, SQL Injection, XSS, CSRF, аутентификация.",
                 "Умение проводить аудит безопасности веб-приложений."),
            disc("Сетевая безопасность", "Б1.В.05", p5, t5, t2,
                 "Изучить методы обеспечения безопасности компьютерных сетей.",
                 "Межсетевые экраны, IDS/IPS, VPN, анализ трафика.",
                 "Умение проектировать защищённые сетевые инфраструктуры."),

            disc("Глубокое обучение", "М2.В.03", p6, t2, t1,
                 "Изучить архитектуры глубоких нейронных сетей.",
                 "CNN, RNN, Transformer, PyTorch, TensorFlow, fine-tuning.",
                 "Умение разрабатывать и обучать модели глубокого обучения."),
            disc("Компьютерное зрение", "М2.В.04", p6, t1, t2,
                 "Изучить методы обработки изображений и компьютерного зрения.",
                 "OpenCV, детекция объектов, сегментация, YOLO, Detectron.",
                 "Умение разрабатывать системы компьютерного зрения."),

            disc("Корпоративные информационные системы", "Б2.О.03", p7, t6, t1,
                 "Изучить архитектуру и внедрение корпоративных ИС.",
                 "ERP, CRM, 1С, SAP, интеграция систем, API.",
                 "Умение настраивать и адаптировать корпоративные ИС."),
            disc("Мобильная разработка", "Б2.В.02", p7, t5, t2,
                 "Освоить разработку мобильных приложений.",
                 "Android/iOS, Kotlin, Swift, React Native, Flutter.",
                 "Умение самостоятельно разрабатывать мобильные приложения."),
            disc("Архитектура ЭВМ и системное программирование", "Б3.О.02", p8, t6, t5,
                 "Изучить аппаратную архитектуру и системное программирование.",
                 "Процессоры, память, ассемблер, драйверы, RTOS.",
                 "Умение разрабатывать системное ПО для встраиваемых систем."),
        ]
        db.add_all(cs_disciplines)
        await db.flush()

        # ── Дисциплины других кафедр ──────────────────────────────────────────
        def ext_disc(name, code, program, dept, t_primary, t_secondary):
            return Discipline(
                name=name, code=code,
                program_id=program.id, department_id=dept.id,
                teacher_primary_id=t_primary.id,
                teacher_secondary_id=t_secondary.id,
            )

        ext_disciplines = [
            ext_disc("Высшая математика",           "Б1.О.01", p1, dept_math,    t3, t4),
            ext_disc("Дискретная математика",        "Б1.О.03", p1, dept_math,    t4, t3),
            ext_disc("Линейная алгебра",             "Б1.О.02", p2, dept_math,    t3, t4),
            ext_disc("Теория графов",                "Б1.О.04", p2, dept_math,    t4, t3),
            ext_disc("Физика",                       "Б1.О.02", p1, dept_physics, t7, t3),
            ext_disc("Квантовые вычисления",         "М1.О.05", p6, dept_physics, t7, t4),
            ext_disc("Экономика программного проекта","Б1.В.10", p4, dept_econ,   t8, t6),
            ext_disc("Менеджмент в IT",              "М1.В.06", p3, dept_econ,    t8, t5),
        ]
        db.add_all(ext_disciplines)
        await db.flush()

        # ── Тестовые данные модуля РОП ────────────────────────────────────────
        # Программы для демо-аккаунта rop@vgtu.ru
        rop_p1 = EducationalProgram(
            name="Информатика и вычислительная техника",
            code="09.03.01", level=ProgramLevel.bachelor, start_year=2022,
            director_id=rop_user.id, department_id=dept_cs.id,
            description="Подготовка специалистов в области разработки ПО и информационных систем.",
            education_form=EducationFormEnum.full_time, education_duration="4 года",
            activity_types="Проектирование ИС, разработка ПО, системный анализ.",
            structure_text="Дисциплины базовой и вариативной частей, практики, ГИА.",
            practices="Производственная практика (4 нед.), преддипломная практика (6 нед.).",
        )
        rop_p2 = EducationalProgram(
            name="Программная инженерия", code="09.03.04",
            level=ProgramLevel.bachelor, start_year=2023,
            director_id=rop_user.id, department_id=dept_cs.id,
            description="Подготовка инженеров-программистов для промышленной разработки ПО.",
            education_form=EducationFormEnum.full_time, education_duration="4 года",
        )
        db.add_all([rop_p1, rop_p2])
        await db.flush()

        # Справочник компетенций
        comps = [
            Competency(code="УК-1",  description="Системное и критическое мышление",                      type=CompetencyType.uk),
            Competency(code="УК-2",  description="Разработка и реализация проектов",                       type=CompetencyType.uk),
            Competency(code="УК-3",  description="Командная работа и лидерство",                           type=CompetencyType.uk),
            Competency(code="ОПК-1", description="Математический аппарат для профессиональных задач",      type=CompetencyType.opk),
            Competency(code="ОПК-2", description="Применение инструментов разработки ПО",                  type=CompetencyType.opk),
            Competency(code="ОПК-3", description="Проектирование и разработка программных систем",         type=CompetencyType.opk),
            Competency(code="ПК-1",  description="Разработка алгоритмов и программных решений",            type=CompetencyType.pk),
            Competency(code="ПК-2",  description="Проектирование баз данных и информационных систем",      type=CompetencyType.pk),
            Competency(code="ПК-3",  description="Тестирование и верификация программного обеспечения",    type=CompetencyType.pk),
        ]
        db.add_all(comps)
        await db.flush()

        # Привязка компетенций к программе 1 (ИВТ)
        for c in comps:
            db.add(ProgramCompetency(program_id=rop_p1.id, competency_id=c.id))

        # Дисциплины (текстовый список) для программы 1
        disc_names_rop = [
            "Базы данных", "Алгоритмы и структуры данных",
            "Объектно-ориентированное программирование", "Операционные системы",
            "Компьютерные сети", "Разработка веб-приложений",
        ]
        for i, name in enumerate(disc_names_rop):
            db.add(ProgramDisciplineItem(program_id=rop_p1.id, name=name, order_index=i))

        await db.flush()

        # ── Чеклист и статус для первой дисциплины (Базы данных) ─────────────
        cat1 = ChecklistCategory(name="РПД", discipline_id=cs_disciplines[0].id, created_by_id=head.id)
        cat2 = ChecklistCategory(name="ФОС", discipline_id=cs_disciplines[0].id, created_by_id=head.id)
        db.add_all([cat1, cat2])
        await db.flush()
        db.add_all([
            ChecklistItem(title="Рабочая программа утверждена",       is_done=True,  category_id=cat1.id, created_by_id=head.id),
            ChecklistItem(title="Учебный план согласован",            is_done=True,  category_id=cat1.id, created_by_id=head.id),
            ChecklistItem(title="Фонд оценочных средств актуализирован", is_done=False, category_id=cat2.id, created_by_id=head.id),
            ChecklistItem(title="Лекционные материалы в LMS",         is_done=True,  category_id=cat2.id, created_by_id=head.id, comment="Загружено в Moodle"),
        ])
        db.add(ReportStatus(discipline_id=cs_disciplines[0].id, status=ReportStatusEnum.draft))

        await db.commit()

    print("✓ БД успешно заполнена")
    print(f"  Программ:   10")
    print(f"  Дисциплин ИВТ: {len(cs_disciplines)}  |  внешних: {len(ext_disciplines)}")
    print("\nВход:")
    print("  Заведующий кафедрой:   head@vgtu.ru / password123")
    print("  Руководитель ОП (РОП): rop@vgtu.ru  / password123")
    print("  Преподаватель:         teacher1@vgtu.ru / password123")


if __name__ == "__main__":
    asyncio.run(seed())
