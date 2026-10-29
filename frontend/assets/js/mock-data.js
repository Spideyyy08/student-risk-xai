/**
 * Realistic Dynamic Mock Data Engine for Vishwakarma Institute of Technology
 * Computer Engineering, Group SEDA-A8
 * Includes Multi-Semester support (Sem 5 AY 2026-27 & Sem 4 AY 2025-26),
 * Dynamic division breakdowns, and individualized role-based views.
 */
(function(window) {
  'use strict';

  // Semester 5 Subjects (Current AY 2026-27)
  const SUBJECTS_SEM5 = [
    { code: 'CS301', name: 'Data Structures & Algorithms', short: 'DSA', maxQuiz: 100, maxInternal: 30 },
    { code: 'CS302', name: 'Database Management Systems', short: 'DBMS', maxQuiz: 100, maxInternal: 30 },
    { code: 'CS303', name: 'Discrete Mathematics', short: 'DM', maxQuiz: 100, maxInternal: 30 },
    { code: 'CS304', name: 'Computer Organization & Architecture', short: 'COA', maxQuiz: 100, maxInternal: 30 },
    { code: 'CS305', name: 'Python Programming', short: 'Python', maxQuiz: 100, maxInternal: 30 }
  ];

  // Semester 4 Subjects (Past AY 2025-26)
  const SUBJECTS_SEM4 = [
    { code: 'CS201', name: 'Object Oriented Programming with Java', short: 'Java', maxQuiz: 100, maxInternal: 30 },
    { code: 'CS202', name: 'Operating Systems', short: 'OS', maxQuiz: 100, maxInternal: 30 },
    { code: 'CS203', name: 'Microprocessor Architecture', short: 'Micro', maxQuiz: 100, maxInternal: 30 },
    { code: 'CS204', name: 'Software Engineering & Agile', short: 'SE', maxQuiz: 100, maxInternal: 30 },
    { code: 'CS205', name: 'Computer Networks Fundamentals', short: 'CN', maxQuiz: 100, maxInternal: 30 }
  ];

  const MONTHS_SEM5 = ['May 2026', 'Jun 2026', 'Jul 2026', 'Aug 2026', 'Sep 2026', 'Oct 2026'];
  const MONTHS_SEM4 = ['Dec 2025', 'Jan 2026', 'Feb 2026', 'Mar 2026', 'Apr 2026', 'May 2026'];

  // Base student roster across SEDA-A and SEDA-B (15 in SEDA-A, 15 in SEDA-B)
  const rawStudentListSem5 = [
    { id: 'STU101', roll: '221101', name: 'Aditya Kulkarni', division: 'SEDA-A', risk: 'High', att: 54, quiz: 46, assign: 50, internal: 14, prac: 16, backlogs: 2, keyFactor: 'Critical Attendance (54%) & 2 Backlogs' },
    { id: 'STU102', roll: '221102', name: 'Ananya Deshpande', division: 'SEDA-A', risk: 'Low', att: 92, quiz: 88, assign: 95, internal: 28, prac: 29, backlogs: 0, keyFactor: 'Consistent High Assessment Scores' },
    { id: 'STU103', roll: '221103', name: 'Rohan Joshi', division: 'SEDA-A', risk: 'High', att: 58, quiz: 42, assign: 55, internal: 13, prac: 18, backlogs: 1, keyFactor: 'Low Quiz Average in DSA & DM' },
    { id: 'STU104', roll: '221104', name: 'Pooja Patil', division: 'SEDA-A', risk: 'Medium', att: 72, quiz: 64, assign: 78, internal: 21, prac: 22, backlogs: 0, keyFactor: 'Drop in Mid-Semester Attendance' },
    { id: 'STU105', roll: '221105', name: 'Siddharth Shinde', division: 'SEDA-A', risk: 'Low', att: 89, quiz: 84, assign: 90, internal: 26, prac: 27, backlogs: 0, keyFactor: 'Strong Practical Performance' },
    { id: 'STU106', roll: '221106', name: 'Neha More', division: 'SEDA-A', risk: 'High', att: 51, quiz: 48, assign: 45, internal: 12, prac: 15, backlogs: 2, keyFactor: 'Chronic Absenteeism & Missed Labs' },
    { id: 'STU107', roll: '221107', name: 'Chinmay Gaikwad', division: 'SEDA-A', risk: 'Medium', att: 68, quiz: 61, assign: 70, internal: 19, prac: 20, backlogs: 1, keyFactor: 'Past Semester SGPA Dip' },
    { id: 'STU108', roll: '221108', name: 'Tanvi Bhosale', division: 'SEDA-A', risk: 'Low', att: 95, quiz: 91, assign: 96, internal: 29, prac: 29, backlogs: 0, keyFactor: 'Top Quartile Across All Subjects' },
    { id: 'STU109', roll: '221109', name: 'Omkar Pawar', division: 'SEDA-A', risk: 'High', att: 59, quiz: 50, assign: 52, internal: 15, prac: 17, backlogs: 1, keyFactor: 'Quiz Score in DSA (50/100)' },
    { id: 'STU110', roll: '221110', name: 'Rutuja Jadhav', division: 'SEDA-A', risk: 'Medium', att: 74, quiz: 67, assign: 75, internal: 22, prac: 23, backlogs: 0, keyFactor: 'Assignment Delays in COA' },
    { id: 'STU111', roll: '221111', name: 'Prathamesh Kadam', division: 'SEDA-A', risk: 'Low', att: 88, quiz: 82, assign: 86, internal: 25, prac: 26, backlogs: 0, keyFactor: 'Steady Academic Progress' },
    { id: 'STU112', roll: '221112', name: 'Sayali Sawant', division: 'SEDA-A', risk: 'Medium', att: 70, quiz: 63, assign: 68, internal: 20, prac: 21, backlogs: 0, keyFactor: 'Declining Trend in Discrete Maths' },
    { id: 'STU113', roll: '221113', name: 'Saurabh Salunkhe', division: 'SEDA-A', risk: 'High', att: 56, quiz: 45, assign: 48, internal: 14, prac: 16, backlogs: 2, keyFactor: 'Low Internal Test Scores' },
    { id: 'STU114', roll: '221114', name: 'Shruti Chitale', division: 'SEDA-A', risk: 'Low', att: 94, quiz: 89, assign: 92, internal: 27, prac: 28, backlogs: 0, keyFactor: 'High Lab Submissions on Time' },
    { id: 'STU115', roll: '221115', name: 'Gaurav Thorat', division: 'SEDA-A', risk: 'Medium', att: 73, quiz: 65, assign: 72, internal: 21, prac: 22, backlogs: 0, keyFactor: 'Borderline Test Scores in DBMS' },
    { id: 'STU116', roll: '221201', name: 'Manish Verma', division: 'SEDA-B', risk: 'High', att: 52, quiz: 44, assign: 46, internal: 13, prac: 15, backlogs: 2, keyFactor: 'Attendance Deficit (<60%)' },
    { id: 'STU117', roll: '221202', name: 'Priyanka Iyer', division: 'SEDA-B', risk: 'Low', att: 91, quiz: 87, assign: 94, internal: 28, prac: 28, backlogs: 0, keyFactor: 'Consistent High Marks in DSA' },
    { id: 'STU118', roll: '221203', name: 'Vikram Choudhary', division: 'SEDA-B', risk: 'High', att: 57, quiz: 47, assign: 54, internal: 15, prac: 17, backlogs: 1, keyFactor: 'Multiple Backlogs Warning' },
    { id: 'STU119', roll: '221204', name: 'Isha Nair', division: 'SEDA-B', risk: 'Medium', att: 75, quiz: 68, assign: 74, internal: 22, prac: 23, backlogs: 0, keyFactor: 'Fluctuating Quiz Performance' },
    { id: 'STU120', roll: '221205', name: 'Kunal Sonawane', division: 'SEDA-B', risk: 'Low', att: 87, quiz: 80, assign: 88, internal: 25, prac: 26, backlogs: 0, keyFactor: 'Strong Practical Aptitude' },
    { id: 'STU121', roll: '221206', name: 'Devendra Mahajan', division: 'SEDA-B', risk: 'High', att: 53, quiz: 43, assign: 49, internal: 12, prac: 16, backlogs: 2, keyFactor: 'Missed Multiple Internal Tests' },
    { id: 'STU122', roll: '221207', name: 'Aishwarya Muley', division: 'SEDA-B', risk: 'Low', att: 93, quiz: 86, assign: 91, internal: 27, prac: 28, backlogs: 0, keyFactor: 'Exemplary Attendance (93%)' },
    { id: 'STU123', roll: '221208', name: 'Yashwardhan Rane', division: 'SEDA-B', risk: 'Medium', att: 69, quiz: 62, assign: 71, internal: 19, prac: 21, backlogs: 1, keyFactor: 'Backlog in Discrete Maths' },
    { id: 'STU124', roll: '221209', name: 'Swati Kulkarni', division: 'SEDA-B', risk: 'Low', att: 96, quiz: 93, assign: 98, internal: 30, prac: 29, backlogs: 0, keyFactor: 'Top Performer in Division B' },
    { id: 'STU125', roll: '221210', name: 'Akshay Tambe', division: 'SEDA-B', risk: 'High', att: 55, quiz: 49, assign: 51, internal: 14, prac: 16, backlogs: 1, keyFactor: 'Low Quiz Average in COA' },
    { id: 'STU126', roll: '221211', name: 'Pallavi Gokhale', division: 'SEDA-B', risk: 'Medium', att: 71, quiz: 66, assign: 73, internal: 21, prac: 22, backlogs: 0, keyFactor: 'Incomplete Practical Journals' },
    { id: 'STU127', roll: '221212', name: 'Nikhil Nalawade', division: 'SEDA-B', risk: 'Low', att: 86, quiz: 81, assign: 85, internal: 24, prac: 25, backlogs: 0, keyFactor: 'Regular Academic Record' },
    { id: 'STU128', roll: '221213', name: 'Kavita Hegde', division: 'SEDA-B', risk: 'Medium', att: 76, quiz: 69, assign: 77, internal: 23, prac: 24, backlogs: 0, keyFactor: 'Moderate Attendance Buffer' },
    { id: 'STU129', roll: '221214', name: 'Sameer Bapat', division: 'SEDA-B', risk: 'High', att: 50, quiz: 40, assign: 42, internal: 11, prac: 14, backlogs: 3, keyFactor: '3 Active Backlogs & Poor Exam Mark' },
    { id: 'STU130', roll: '221215', name: 'Mugdha Chiplunkar', division: 'SEDA-B', risk: 'Low', att: 90, quiz: 85, assign: 92, internal: 26, prac: 27, backlogs: 0, keyFactor: 'Consistent Lab Submissions' }
  ];

  // Semester 4 Historical baseline with different outcomes
  const rawStudentListSem4 = rawStudentListSem5.map(s => {
    // In Sem 4, overall risk was slightly lower before advanced courses
    let sem4Risk = s.risk;
    let sem4Att = Math.min(98, s.att + 6);
    let sem4Quiz = Math.min(96, s.quiz + 5);
    let sem4Backlogs = Math.max(0, s.backlogs - 1);

    if (sem4Att > 75 && sem4Quiz > 68 && sem4Backlogs === 0) {
      sem4Risk = 'Low';
    } else if (sem4Att < 65 || sem4Backlogs >= 2) {
      sem4Risk = 'High';
    } else {
      sem4Risk = 'Medium';
    }

    return {
      ...s,
      risk: sem4Risk,
      att: sem4Att,
      quiz: sem4Quiz,
      backlogs: sem4Backlogs,
      keyFactor: sem4Risk === 'High' ? 'Operating Systems Lab Absences' : (sem4Risk === 'Medium' ? 'Mid-Sem OOP Java Exam' : 'Satisfactory Performance')
    };
  });

  function generateProbabilities(risk, att, quiz, backlogs) {
    let pHigh = 0.1, pMed = 0.2, pLow = 0.7;
    if (risk === 'High') {
      pHigh = Math.min(0.92, 0.65 + (70 - att) * 0.005 + (50 - quiz) * 0.004 + backlogs * 0.05);
      pMed = Math.max(0.06, 0.95 - pHigh);
      pLow = Math.max(0.02, 1.0 - pHigh - pMed);
    } else if (risk === 'Medium') {
      pMed = 0.60;
      pHigh = 0.22;
      pLow = 0.18;
    } else {
      pLow = Math.min(0.94, 0.70 + (att - 75) * 0.008 + (quiz - 70) * 0.005);
      pMed = Math.max(0.05, 0.96 - pLow);
      pHigh = Math.max(0.01, 1.0 - pLow - pMed);
    }
    const sum = pLow + pMed + pHigh;
    return {
      low: Number((pLow / sum).toFixed(2)),
      medium: Number((pMed / sum).toFixed(2)),
      high: Number((pHigh / sum).toFixed(2))
    };
  }

  function transformList(rawList, semName) {
    return rawList.map(st => {
      const probs = generateProbabilities(st.risk, st.att, st.quiz, st.backlogs);
      return {
        id: st.id,
        roll: st.roll,
        name: st.name,
        division: st.division,
        semester: semName,
        risk_level: st.risk,
        probabilities: probs,
        updated_at: '2026-10-28',
        attendance_pct: st.att,
        quiz_avg: st.quiz,
        assignment_pct: st.assign,
        internal_marks: st.internal,
        practical_marks: st.prac,
        backlogs: st.backlogs,
        key_factor: st.keyFactor,
        past_sgpa: [
          { semester: 'Sem 3', sgpa: st.risk === 'High' ? 6.12 : (st.risk === 'Medium' ? 7.24 : 8.85) },
          { semester: 'Sem 4', sgpa: st.risk === 'High' ? 5.84 : (st.risk === 'Medium' ? 7.02 : 8.92) }
        ]
      };
    });
  }

  const STUDENTS_SEM5 = transformList(rawStudentListSem5, 'Semester 5 (AY 2026-27)');
  const STUDENTS_SEM4 = transformList(rawStudentListSem4, 'Semester 4 (AY 2025-26)');

  function getStudentPool(semester = 'sem5') {
    return semester === 'sem4' ? STUDENTS_SEM4 : STUDENTS_SEM5;
  }

  // Interventions Mock Storage
  let INTERVENTIONS = [
    {
      id: 'INT-301',
      student_id: 'STU101',
      student_name: 'Aditya Kulkarni',
      division: 'SEDA-A',
      semester: 'sem5',
      type: 'Parent meeting',
      date: '2026-10-24',
      status: 'In progress',
      notes: 'Discussed severe attendance shortfall (54%) and upcoming remedial sessions for Data Structures.'
    },
    {
      id: 'INT-302',
      student_id: 'STU106',
      student_name: 'Neha More',
      division: 'SEDA-A',
      semester: 'sem5',
      type: 'Counselling',
      date: '2026-10-22',
      status: 'Planned',
      notes: 'Referred to department counselor regarding health-related absences and missed lab journals.'
    },
    {
      id: 'INT-303',
      student_id: 'STU116',
      student_name: 'Manish Verma',
      division: 'SEDA-B',
      semester: 'sem5',
      type: 'Mentor assigned',
      date: '2026-10-18',
      status: 'Completed',
      notes: 'Assigned peer tutor for Discrete Mathematics problem solving sessions every Tuesday.'
    },
    {
      id: 'INT-304',
      student_id: 'STU129',
      student_name: 'Sameer Bapat',
      division: 'SEDA-B',
      semester: 'sem5',
      type: 'Extra class',
      date: '2026-10-15',
      status: 'In progress',
      notes: 'Enrolled in 4-week zero-backlog remedial bridge course for Computer Organization.'
    },
    {
      id: 'INT-305',
      student_id: 'STU103',
      student_name: 'Rohan Joshi',
      division: 'SEDA-A',
      semester: 'sem5',
      type: 'Counselling',
      date: '2026-10-11',
      status: 'Completed',
      notes: 'Reviewed quiz performance in DSA (42/100). Provided curated algorithm practice sheet.'
    },
    {
      id: 'INT-201',
      student_id: 'STU101',
      student_name: 'Aditya Kulkarni',
      division: 'SEDA-A',
      semester: 'sem4',
      type: 'Extra class',
      date: '2026-03-12',
      status: 'Completed',
      notes: 'Completed Java OOP exception handling laboratory bridge classes.'
    }
  ];

  /**
   * Dynamic Class Analytics summary calculations
   * Recalculates dynamically based on active division and semester!
   */
  function getClassSummary(division = 'ALL', semester = 'sem5') {
    let pool = getStudentPool(semester);

    if (division && division !== 'ALL') {
      pool = pool.filter(s => s.division === division);
    }

    const total = pool.length;
    const high = pool.filter(s => s.risk_level === 'High').length;
    const medium = pool.filter(s => s.risk_level === 'Medium').length;
    const low = pool.filter(s => s.risk_level === 'Low').length;

    const divA = pool.filter(s => s.division === 'SEDA-A');
    const divB = pool.filter(s => s.division === 'SEDA-B');

    const by_division = [];
    if (divA.length > 0) {
      by_division.push({
        division: 'SEDA-A',
        total: divA.length,
        high: divA.filter(s => s.risk_level === 'High').length,
        medium: divA.filter(s => s.risk_level === 'Medium').length,
        low: divA.filter(s => s.risk_level === 'Low').length
      });
    }
    if (divB.length > 0) {
      by_division.push({
        division: 'SEDA-B',
        total: divB.length,
        high: divB.filter(s => s.risk_level === 'High').length,
        medium: divB.filter(s => s.risk_level === 'Medium').length,
        low: divB.filter(s => s.risk_level === 'Low').length
      });
    }

    // Dynamic top factors weighting based on semester and division
    let top_factors = [];
    if (semester === 'sem5') {
      top_factors = [
        { factor: 'Attendance < 65%', importance: division === 'SEDA-B' ? 0.38 : 0.33, direction: 'risk_raising' },
        { factor: 'Quiz Average in DSA', importance: division === 'SEDA-A' ? 0.31 : 0.26, direction: 'risk_raising' },
        { factor: 'Prior Semester Backlogs', importance: 0.20, direction: 'risk_raising' },
        { factor: 'Mid-Sem Internal Marks', importance: 0.12, direction: 'risk_neutral' },
        { factor: 'Lab Assignment Submissions', importance: 0.05, direction: 'risk_lowering' }
      ];
    } else {
      top_factors = [
        { factor: 'Operating Systems Attendance', importance: 0.35, direction: 'risk_raising' },
        { factor: 'OOP Java Lab Practical Test', importance: 0.25, direction: 'risk_raising' },
        { factor: 'Discrete Mathematics Backlog', importance: 0.22, direction: 'risk_raising' },
        { factor: 'Microprocessor Internal Exam', importance: 0.10, direction: 'risk_neutral' },
        { factor: 'Software Engineering Project', importance: 0.08, direction: 'risk_lowering' }
      ];
    }

    return {
      total,
      high,
      high_pct: total > 0 ? Math.round((high / total) * 100) : 0,
      medium,
      medium_pct: total > 0 ? Math.round((medium / total) * 100) : 0,
      low,
      low_pct: total > 0 ? Math.round((low / total) * 100) : 0,
      by_division,
      top_factors,
      semester,
      division
    };
  }

  function getStudentExplanations(student) {
    const isHigh = student.risk_level === 'High';
    const isLow = student.risk_level === 'Low';
    const base_value = 0.28;

    const attDev = 75 - student.attendance_pct;
    const attShap = Number((attDev * 0.006).toFixed(3));

    const quizDev = 65 - student.quiz_avg;
    const quizShap = Number((quizDev * 0.005).toFixed(3));

    const backlogShap = Number((student.backlogs * 0.09).toFixed(3));

    const assignDev = 75 - student.assignment_pct;
    const assignShap = Number((assignDev * 0.003).toFixed(3));

    const internalDev = 20 - student.internal_marks;
    const internalShap = Number((internalDev * 0.005).toFixed(3));

    const sgpaShap = isHigh ? 0.045 : (isLow ? -0.055 : 0.010);

    return {
      base_value,
      factors: [
        {
          feature: 'overall_attendance',
          label: 'Overall Attendance',
          value: `${student.attendance_pct}%`,
          shap: attShap,
          detail: student.attendance_pct < 65 ? 'Below 65% mandatory threshold' : 'Regular class attendance'
        },
        {
          feature: 'quiz_average',
          label: 'Continuous Assessment Quiz Average',
          value: `${student.quiz_avg}/100`,
          shap: quizShap,
          detail: student.quiz_avg < 50 ? 'Sub-50% average across subjects' : 'Satisfactory test performance'
        },
        {
          feature: 'active_backlogs',
          label: 'Active Backlog Count',
          value: `${student.backlogs} courses`,
          shap: backlogShap,
          detail: student.backlogs > 0 ? 'Carrying forward uncleared courses' : 'Zero outstanding backlogs'
        },
        {
          feature: 'assignment_completion',
          label: 'Assignment & Journal Submissions',
          value: `${student.assignment_pct}%`,
          shap: assignShap,
          detail: student.assignment_pct < 70 ? 'Missing lab code evaluations' : 'On-time assignment submissions'
        },
        {
          feature: 'internal_marks',
          label: 'Mid-Sem Internal Marks',
          value: `${student.internal_marks}/30`,
          shap: internalShap,
          detail: 'Cumulative internal test score'
        },
        {
          feature: 'prior_academic_momentum',
          label: 'Past Semester SGPA Momentum',
          value: `${student.past_sgpa[1].sgpa} SGPA`,
          shap: sgpaShap,
          detail: 'Trajectory between Sem 3 and Sem 4'
        }
      ]
    };
  }

  function getStudentSubjects(student, semester = 'sem5') {
    const subjects = semester === 'sem4' ? SUBJECTS_SEM4 : SUBJECTS_SEM5;

    return subjects.map((s, idx) => {
      const offset = (idx % 3 === 0) ? -5 : (idx % 2 === 0 ? 3 : -2);
      const att = Math.max(38, Math.min(99, student.attendance_pct + offset));
      const quiz = Math.max(32, Math.min(98, student.quiz_avg + (idx === 0 ? -6 : offset)));
      const assign = Math.max(40, Math.min(100, student.assignment_pct + offset));
      const internal = Math.max(8, Math.min(30, Math.round(student.internal_marks + offset * 0.2)));

      let status = 'Satisfactory';
      if (att < 60 || quiz < 50 || internal < 14) {
        status = 'Critical';
      } else if (att < 75 || quiz < 65 || internal < 18) {
        status = 'Attention';
      }

      return {
        subject_code: s.code,
        subject_name: s.name,
        subject_short: s.short,
        attendance_pct: att,
        quiz_avg: quiz,
        quiz_max: 100,
        assignment_pct: assign,
        internal_marks: internal,
        internal_max: 30,
        status: status
      };
    });
  }

  function getStudentTrends(student, semester = 'sem5') {
    const attBase = student.attendance_pct;
    const quizBase = student.quiz_avg;
    const months = semester === 'sem4' ? MONTHS_SEM4 : MONTHS_SEM5;

    let attTrajectory = [];
    let quizTrajectory = [];

    if (student.risk_level === 'High') {
      attTrajectory = [attBase + 14, attBase + 10, attBase + 7, attBase + 3, attBase - 1, attBase];
      quizTrajectory = [quizBase + 10, quizBase + 8, quizBase + 4, quizBase + 2, quizBase - 1, quizBase];
    } else if (student.risk_level === 'Medium') {
      attTrajectory = [attBase - 2, attBase + 4, attBase - 3, attBase + 1, attBase - 2, attBase];
      quizTrajectory = [quizBase + 3, quizBase - 4, quizBase + 2, quizBase - 2, quizBase + 1, quizBase];
    } else {
      attTrajectory = [attBase - 2, attBase - 1, attBase + 1, attBase, attBase + 2, attBase];
      quizTrajectory = [quizBase - 3, quizBase, quizBase + 1, quizBase + 2, quizBase + 1, quizBase];
    }

    return {
      months: months,
      attendance: attTrajectory.map(v => Math.max(35, Math.min(99, Math.round(v)))),
      quiz_scores: quizTrajectory.map(v => Math.max(30, Math.min(100, Math.round(v)))),
      past_sgpa: student.past_sgpa
    };
  }

  function getStudentRecommendations(student) {
    const recs = [];

    if (student.attendance_pct < 65) {
      recs.push({
        priority: 'High',
        action: 'Mandatory remedial attendance recovery contract: Attend 12 scheduled Saturday tutorial batches',
        reason: `Overall attendance has fallen to ${student.attendance_pct}%, violating the 75% institute guideline.`,
        subject: 'General / All Subjects',
        assigned: true
      });
    }

    if (student.quiz_avg < 55) {
      recs.push({
        priority: 'High',
        action: 'Complete 5 easy, 5 medium and 5 hard sorting & graph algorithm problem sets on HackerRank',
        reason: `Quiz average in Data Structures & Algorithms is currently ${Math.max(35, student.quiz_avg - 4)}/100.`,
        subject: 'Data Structures & Algorithms',
        assigned: false
      });
    }

    if (student.backlogs > 0) {
      recs.push({
        priority: 'High',
        action: 'Enroll in Faculty Mentorship Backlog Clearance Track for Discrete Mathematics',
        reason: `Student is carrying forward ${student.backlogs} backlog(s) from Sem 3/4.`,
        subject: 'Discrete Mathematics',
        assigned: true
      });
    }

    if (student.assignment_pct < 75) {
      recs.push({
        priority: 'Medium',
        action: 'Submit pending laboratory journals and obtain sign-off from Lab In-charge',
        reason: `Assignment & journal completion is at ${student.assignment_pct}%.`,
        subject: 'Database Management Systems',
        assigned: false
      });
    }

    if (recs.length === 0) {
      recs.push({
        priority: 'Low',
        action: 'Recommend participation in Smart India Hackathon and competitive programming club',
        reason: `High academic consistency across all continuous evaluation metrics.`,
        subject: 'Python Programming',
        assigned: false
      });
      recs.push({
        priority: 'Low',
        action: 'Eligible for Department Honors / Minor degree track in Artificial Intelligence',
        reason: `Maintained SGPA above 8.5 with 0 backlogs.`,
        subject: 'Academic Advising',
        assigned: false
      });
    }

    return recs;
  }

  function simulateWhatIf(studentId, overrides, semester = 'sem5') {
    const pool = getStudentPool(semester);
    const student = pool.find(s => s.id === studentId) || pool[0];

    const att = overrides.attendance_pct !== undefined ? Number(overrides.attendance_pct) : student.attendance_pct;
    const quiz = overrides.quiz_avg !== undefined ? Number(overrides.quiz_avg) : student.quiz_avg;
    const assign = overrides.assignment_pct !== undefined ? Number(overrides.assignment_pct) : student.assignment_pct;
    const internal = overrides.internal_marks !== undefined ? Number(overrides.internal_marks) : student.internal_marks;
    const prac = overrides.practical_marks !== undefined ? Number(overrides.practical_marks) : student.practical_marks;
    const backlogs = overrides.backlogs !== undefined ? Number(overrides.backlogs) : student.backlogs;

    const attRisk = Math.max(0, 100 - att);
    const quizRisk = Math.max(0, 100 - quiz);
    const backlogRisk = Math.min(100, backlogs * 35);
    const internalRisk = Math.max(0, (30 - internal) * (100 / 30));
    const assignRisk = Math.max(0, 100 - assign);

    const compositeScore = (attRisk * 0.30) + (quizRisk * 0.25) + (backlogRisk * 0.20) + (internalRisk * 0.15) + (assignRisk * 0.10);

    let simRisk = 'Low';
    if (compositeScore >= 42 || att < 60 || backlogs >= 2) {
      simRisk = 'High';
    } else if (compositeScore >= 24 || att < 72 || backlogs >= 1) {
      simRisk = 'Medium';
    } else {
      simRisk = 'Low';
    }

    const simProbabilities = generateProbabilities(simRisk, att, quiz, backlogs);

    const attDev = 75 - att;
    const quizDev = 65 - quiz;
    const backlogShap = Number((backlogs * 0.09).toFixed(3));
    const attShap = Number((attDev * 0.006).toFixed(3));
    const quizShap = Number((quizDev * 0.005).toFixed(3));
    const assignDev = 75 - assign;
    const assignShap = Number((assignDev * 0.003).toFixed(3));
    const internalDev = 20 - internal;
    const internalShap = Number((internalDev * 0.005).toFixed(3));

    const simulatedFactors = [
      {
        feature: 'overall_attendance',
        label: 'Overall Attendance',
        value: `${att}%`,
        shap: attShap,
        detail: att < 65 ? 'Below 65% mandatory threshold' : 'Regular class attendance'
      },
      {
        feature: 'quiz_average',
        label: 'Continuous Assessment Quiz Average',
        value: `${quiz}/100`,
        shap: quizShap,
        detail: quiz < 50 ? 'Sub-50% average across subjects' : 'Satisfactory test performance'
      },
      {
        feature: 'active_backlogs',
        label: 'Active Backlog Count',
        value: `${backlogs} courses`,
        shap: backlogShap,
        detail: backlogs > 0 ? 'Carrying forward uncleared courses' : 'Zero outstanding backlogs'
      },
      {
        feature: 'assignment_completion',
        label: 'Assignment & Journal Submissions',
        value: `${assign}%`,
        shap: assignShap,
        detail: assign < 70 ? 'Missing lab code evaluations' : 'On-time assignment submissions'
      },
      {
        feature: 'internal_marks',
        label: 'Mid-Sem Internal Marks',
        value: `${internal}/30`,
        shap: internalShap,
        detail: 'Simulated internal score'
      }
    ];

    return {
      current: {
        student_id: student.id,
        name: student.name,
        roll: student.roll,
        risk_level: student.risk_level,
        probabilities: student.probabilities,
        attendance_pct: student.attendance_pct,
        quiz_avg: student.quiz_avg,
        assignment_pct: student.assignment_pct,
        internal_marks: student.internal_marks,
        practical_marks: student.practical_marks,
        backlogs: student.backlogs
      },
      simulated: {
        risk_level: simRisk,
        probabilities: simProbabilities,
        factors: simulatedFactors
      }
    };
  }

  window.MockData = {
    STUDENTS: STUDENTS_SEM5,
    STUDENTS_SEM5,
    STUDENTS_SEM4,
    INTERVENTIONS,
    SUBJECTS_SEM5,
    SUBJECTS_SEM4,
    MONTHS: MONTHS_SEM5,
    getStudentPool,
    getClassSummary,
    getStudentExplanations,
    getStudentSubjects,
    getStudentTrends,
    getStudentRecommendations,
    simulateWhatIf
  };
})(window);
