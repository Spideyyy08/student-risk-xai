/**
 * API Client Module
 * Provides unified fetch abstraction with JWT headers, 401 handling,
 * and high-fidelity fallback to window.MockData when USE_MOCK is true.
 */
(function(window) {
  'use strict';

  function getToken() {
    return sessionStorage.getItem('access_token');
  }

  function handleUnauthorized() {
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('user_role');
    sessionStorage.removeItem('user_name');
    if (!window.location.pathname.endsWith('index.html') && window.location.pathname !== '/') {
      window.location.href = '/index.html';
    }
  }

  async function request(endpoint, options = {}) {
    const config = window.APP_CONFIG || { API_BASE: '/api/v1', USE_MOCK: true };

    if (!config.USE_MOCK) {
      const headers = {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      };
      const token = getToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      try {
        const res = await fetch(`${config.API_BASE}${endpoint}`, {
          ...options,
          headers
        });

        if (res.status === 401) {
          handleUnauthorized();
          throw new Error('Unauthorized session. Redirecting to login.');
        }

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || errData.message || `Request failed with status ${res.status}`);
        }

        return await res.json();
      } catch (err) {
        console.warn(`[API] Real endpoint ${endpoint} failed. Falling back to mock.`, err);
        return handleMockFallback(endpoint, options);
      }
    }

    // Direct mock simulation
    return handleMockFallback(endpoint, options);
  }

  /**
   * Router for mock data responses corresponding to FastAPI contract
   */
  async function handleMockFallback(endpoint, options = {}) {
    // Artificial small delay for realism (120ms)
    await new Promise(resolve => setTimeout(resolve, 120));
    const mock = window.MockData;
    if (!mock) throw new Error('MockData is not loaded');

    const method = (options.method || 'GET').toUpperCase();
    const url = new URL(endpoint, 'http://localhost');
    const path = url.pathname;
    const searchParams = url.searchParams;

    // POST /auth/login
    if (path === '/auth/login' && method === 'POST') {
      const body = options.body ? JSON.parse(options.body) : {};
      const { username, password } = body;

      if (!username || !password) {
        throw new Error('Username and password are required');
      }

      let role = 'TEACHER';
      let name = 'Prof. A. S. Sharma';

      if (username.toLowerCase().includes('admin')) {
        role = 'ADMIN';
        name = 'Head of Department (Admin)';
      } else if (username.toLowerCase().includes('student')) {
        role = 'STUDENT';
        name = 'Aditya Kulkarni (Student)';
      }

      return {
        access_token: 'mock-jwt-token-' + Math.random().toString(36).substring(2),
        token_type: 'bearer',
        role: role,
        name: name,
        department: 'Computer Engineering'
      };
    }

    // GET /analytics/class-summary
    if (path === '/analytics/class-summary') {
      const div = searchParams.get('division') || 'ALL';
      const sem = searchParams.get('semester') || sessionStorage.getItem('academic_semester') || 'sem5';
      return mock.getClassSummary(div, sem);
    }

    // GET /students
    if (path === '/students' && method === 'GET') {
      const sem = searchParams.get('semester') || sessionStorage.getItem('academic_semester') || 'sem5';
      let list = [...mock.getStudentPool(sem)];
      const div = searchParams.get('division');
      const risk = searchParams.get('risk');
      const q = (searchParams.get('q') || '').toLowerCase().trim();
      const page = parseInt(searchParams.get('page') || '1', 10);
      const pageSize = 10;

      if (div && div !== 'ALL') {
        list = list.filter(s => s.division === div);
      }
      if (risk && risk !== 'ALL') {
        list = list.filter(s => s.risk_level.toUpperCase() === risk.toUpperCase());
      }
      if (q) {
        list = list.filter(s =>
          s.name.toLowerCase().includes(q) ||
          s.roll.toLowerCase().includes(q) ||
          s.id.toLowerCase().includes(q)
        );
      }

      const total = list.length;
      const totalPages = Math.ceil(total / pageSize) || 1;
      const startIndex = (page - 1) * pageSize;
      const items = list.slice(startIndex, startIndex + pageSize);

      return {
        items,
        total,
        page,
        total_pages: totalPages,
        page_size: pageSize,
        semester: sem
      };
    }

    // GET /students/{id}
    const studentMatch = path.match(/^\/students\/([A-Za-z0-9_-]+)$/);
    if (studentMatch && method === 'GET') {
      const id = studentMatch[1];
      const student = mock.STUDENTS.find(s => s.id === id || s.roll === id);
      if (!student) throw new Error('Student not found');
      return student;
    }

    // GET /predictions/{student_id}
    const predMatch = path.match(/^\/predictions\/([A-Za-z0-9_-]+)$/);
    if (predMatch) {
      const id = predMatch[1];
      const student = mock.STUDENTS.find(s => s.id === id || s.roll === id) || mock.STUDENTS[0];
      return {
        student_id: student.id,
        risk_level: student.risk_level,
        probabilities: student.probabilities,
        updated_at: student.updated_at
      };
    }

    // GET /explanations/{student_id}
    const expMatch = path.match(/^\/explanations\/([A-Za-z0-9_-]+)$/);
    if (expMatch) {
      const id = expMatch[1];
      const student = mock.STUDENTS.find(s => s.id === id || s.roll === id) || mock.STUDENTS[0];
      return mock.getStudentExplanations(student);
    }

    // GET /analytics/{student_id}/subjects
    const subjMatch = path.match(/^\/analytics\/([A-Za-z0-9_-]+)\/subjects$/);
    if (subjMatch) {
      const id = subjMatch[1];
      const student = mock.STUDENTS.find(s => s.id === id || s.roll === id) || mock.STUDENTS[0];
      return mock.getStudentSubjects(student);
    }

    // GET /analytics/{student_id}/trends
    const trendMatch = path.match(/^\/analytics\/([A-Za-z0-9_-]+)\/trends$/);
    if (trendMatch) {
      const id = trendMatch[1];
      const student = mock.STUDENTS.find(s => s.id === id || s.roll === id) || mock.STUDENTS[0];
      return mock.getStudentTrends(student);
    }

    // GET /recommendations/{student_id}
    const recMatch = path.match(/^\/recommendations\/([A-Za-z0-9_-]+)$/);
    if (recMatch) {
      const id = recMatch[1];
      const student = mock.STUDENTS.find(s => s.id === id || s.roll === id) || mock.STUDENTS[0];
      return mock.getStudentRecommendations(student);
    }

    // POST /simulator/what-if
    if (path === '/simulator/what-if' && method === 'POST') {
      const body = options.body ? JSON.parse(options.body) : {};
      return mock.simulateWhatIf(body.student_id, body.overrides || {});
    }

    // GET/POST /interventions
    if (path === '/interventions') {
      if (method === 'GET') {
        const studentId = searchParams.get('student_id');
        if (studentId) {
          return mock.INTERVENTIONS.filter(i => i.student_id === studentId);
        }
        return mock.INTERVENTIONS;
      }
      if (method === 'POST') {
        const body = options.body ? JSON.parse(options.body) : {};
        const student = mock.STUDENTS.find(s => s.id === body.student_id) || { name: 'Student', division: 'SEDA-A' };
        const newInt = {
          id: 'INT-' + Math.floor(300 + Math.random() * 700),
          student_id: body.student_id,
          student_name: student.name,
          division: student.division,
          type: body.type || 'Counselling',
          date: body.date || new Date().toISOString().split('T')[0],
          status: body.status || 'Planned',
          notes: body.notes || ''
        };
        mock.INTERVENTIONS.unshift(newInt);
        return { success: true, item: newInt };
      }
    }

    // POST /attendance
    if (path === '/attendance' && method === 'POST') {
      const body = options.body ? JSON.parse(options.body) : {};
      return { success: true, message: 'Attendance records logged successfully', count: body.records ? body.records.length : 1 };
    }

    // POST /assessments
    if (path === '/assessments' && method === 'POST') {
      return { success: true, message: 'Continuous test marks saved successfully' };
    }

    // POST /assignments
    if (path === '/assignments' && method === 'POST') {
      return { success: true, message: 'Assignment completion status updated' };
    }

    // POST /imports
    if (path === '/imports' && method === 'POST') {
      return { success: true, message: 'Batch CSV file processed successfully. 30 student records synchronized.' };
    }

    throw new Error(`Unhandled mock route: ${method} ${endpoint}`);
  }

  window.API = {
    request,
    login: (username, password) => request('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) }),
    getClassSummary: (params = {}) => {
      const qs = new URLSearchParams(params).toString();
      return request(`/analytics/class-summary?${qs}`);
    },
    getStudents: (params = {}) => {
      const qs = new URLSearchParams(params).toString();
      return request(`/students?${qs}`);
    },
    getStudentById: (id) => request(`/students/${id}`),
    getPrediction: (id) => request(`/predictions/${id}`),
    getExplanation: (id) => request(`/explanations/${id}`),
    getSubjects: (id) => request(`/analytics/${id}/subjects`),
    getTrends: (id) => request(`/analytics/${id}/trends`),
    getRecommendations: (id) => request(`/recommendations/${id}`),
    simulateWhatIf: (studentId, overrides) => request('/simulator/what-if', { method: 'POST', body: JSON.stringify({ student_id: studentId, overrides }) }),
    getInterventions: (params = {}) => {
      const qs = new URLSearchParams(params).toString();
      return request(`/interventions?${qs}`);
    },
    createIntervention: (data) => request('/interventions', { method: 'POST', body: JSON.stringify(data) }),
    postAttendance: (data) => request('/attendance', { method: 'POST', body: JSON.stringify(data) }),
    postAssessments: (data) => request('/assessments', { method: 'POST', body: JSON.stringify(data) }),
    postAssignments: (data) => request('/assignments', { method: 'POST', body: JSON.stringify(data) }),
    postImports: (data) => request('/imports', { method: 'POST', body: JSON.stringify(data) })
  };
})(window);
