import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AdminRoute } from './components/AdminRoute';

import { Home } from './pages/Home';
import { Exams } from './pages/Exams';
import { ExamDetails } from './pages/ExamDetails';
import { MockPayment } from './pages/MockPayment';
import { Instructions } from './pages/Instructions';
import { ExamEngine } from './pages/ExamEngine';
import { Result } from './pages/Result';
import { Dashboard } from './pages/Dashboard';
import { About } from './pages/About';
import { Login } from './pages/Login';
import { Register } from './pages/Register';

import { AdminDashboard } from './pages/admin/AdminDashboard';
import { AdminExams } from './pages/admin/AdminExams';
import { AdminTests } from './pages/admin/AdminTests';
import { AdminQuestions } from './pages/admin/AdminQuestions';
import { AdminStudents } from './pages/admin/AdminStudents';
import { AdminPayments } from './pages/admin/AdminPayments';
import { AdminScheduler } from './pages/admin/AdminScheduler';


import { PastYearPapersPage } from './pages/PastYearPapers';
import { AdminPastYearPapers } from './pages/admin/AdminPastYearPapers';


export const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen flex flex-col bg-gray-50">
          <Routes>
            {/* Full-screen Exam Engine route without navbar/footer clutter */}
            <Route
              path="/exam/:attemptId"
              element={
                <ProtectedRoute>
                  <ExamEngine />
                </ProtectedRoute>
              }
            />
            <Route
              path="/exam-engine/:attemptId"
              element={
                <ProtectedRoute>
                  <ExamEngine />
                </ProtectedRoute>
              }
            />

            {/* Standard Layout Routes */}
            <Route
              path="*"
              element={
                <>
                  <Navbar />
                  <main className="flex-1">
                    <Routes>
                      <Route path="/" element={<Home />} />
                      <Route path="/exams" element={<Exams />} />
                      <Route path="/exams/:examId" element={<ExamDetails />} />
                      <Route path="/about" element={<About />} />
                      <Route path="/login" element={<Login />} />
                      <Route path="/register" element={<Register />} />

                      <Route path="/past-year-papers" element={<PastYearPapersPage />} />

                      {/* Protected Student Routes */}
                      <Route
                        path="/payment/mock"
                        element={
                          <ProtectedRoute>
                            <MockPayment />
                          </ProtectedRoute>
                        }
                      />
                      <Route
                        path="/instructions/:testId"
                        element={
                          <ProtectedRoute>
                            <Instructions />
                          </ProtectedRoute>
                        }
                      />
                      <Route
                        path="/result/:attemptId"
                        element={
                          <ProtectedRoute>
                            <Result />
                          </ProtectedRoute>
                        }
                      />
                      <Route
                        path="/dashboard"
                        element={
                          <ProtectedRoute>
                            <Dashboard />
                          </ProtectedRoute>
                        }
                      />

                      {/* Protected Admin Portal Routes */}
                      <Route
                        path="/admin"
                        element={
                          <AdminRoute>
                            <AdminDashboard />
                          </AdminRoute>
                        }
                      />
                      <Route
                        path="/admin/past-year-papers"
                        element={
                          <AdminRoute>
                            <AdminPastYearPapers />
                          </AdminRoute>
                        }
                      />
                      <Route
                        path="/admin/exams"
                        element={
                          <AdminRoute>
                            <AdminExams />
                          </AdminRoute>
                        }
                      />
                      <Route
                        path="/admin/tests"
                        element={
                          <AdminRoute>
                            <AdminTests />
                          </AdminRoute>
                        }
                      />
                      <Route
                        path="/admin/questions"
                        element={
                          <AdminRoute>
                            <AdminQuestions />
                          </AdminRoute>
                        }
                      />
                      <Route
                        path="/admin/students"
                        element={
                          <AdminRoute>
                            <AdminStudents />
                          </AdminRoute>
                        }
                      />
                      <Route
                        path="/admin/payments"
                        element={
                          <AdminRoute>
                            <AdminPayments />
                          </AdminRoute>
                        }
                      />
                      <Route
                        path="/admin/scheduler"
                        element={
                          <AdminRoute>
                            <AdminScheduler />
                          </AdminRoute>
                        }
                      />

                    </Routes>
                  </main>
                  <Footer />
                </>
              }
            />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
};

export default App;
