export type UserRole = 'STUDENT' | 'ADMIN';
export type UserStatus = 'ACTIVE' | 'DISABLED';
export type ExamStatus = 'ACTIVE' | 'INACTIVE';
export type TestStatus = 'PUBLISHED' | 'DRAFT';
export type PaymentStatus = 'PENDING' | 'SUCCESS' | 'FAILED' | 'REFUNDED';
export type PaymentMethod = 'MOCK' | 'ADMIN_GRANTED' | 'RAZORPAY';
export type AttemptStatus = 'IN_PROGRESS' | 'SUBMITTED' | 'EXPIRED';
export type QuestionSetStatus = 'DRAFT' | 'SCHEDULED' | 'ACTIVE' | 'EXPIRED' | 'CANCELLED';
export type PastYearPaperStatus = 'DRAFT' | 'REVIEW' | 'PUBLISHED' | 'ARCHIVED';

export interface User {
  id: number;
  name: string;
  email: string;
  mobile: string;
  role: UserRole;
  status: UserStatus;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  role: UserRole;
  user_id: number;
  name: string;
}

export interface Exam {
  id: number;
  name: string;
  slug: string;
  description?: string;
  price: number;
  language_mode: string; // TA or TA_EN
  status: ExamStatus;
  created_at: string;
}

export interface Test {
  id: number;
  exam_id: number;
  exam_name?: string;
  exam_slug?: string;
  allowed_languages: string[];
  title: string;
  description?: string;
  test_date?: string;
  duration_minutes: number;
  question_count: number;
  price: number;
  status: TestStatus;
  created_at: string;
  has_access?: boolean;
  has_active_set?: boolean;
  active_question_set_id?: number;
  next_publish_info?: string;
}

export interface PastYearPaper {
  id: number;
  exam_id: number;
  year: number;
  title: string;
  description?: string;
  duration_minutes: number;
  question_count: number;
  marks_per_question: number;
  negative_mark: number;
  price: number;
  status: PastYearPaperStatus;
  exam_name?: string;
  exam_slug?: string;
  allowed_languages: string[];
  created_at: string;
  updated_at: string;
  has_access?: boolean;
}

export interface QuestionSet {
  id: number;
  exam_id: number;
  test_id: number;
  exam_name?: string;
  exam_slug?: string;
  test_title?: string;
  title: string;
  schedule_date: string;
  publish_at?: string;
  published_at?: string;
  expire_at?: string;
  expired_at?: string;
  status: QuestionSetStatus;
  question_count: number;
  created_by?: number;
  created_at: string;
  updated_at: string;
}

export interface SchedulerCalendarDay {
  date_str: string;
  day_name: string;
  is_today: boolean;
  is_allowed: boolean;
  sets: QuestionSet[];
}

export interface AuditLog {
  id: number;
  user_id?: number;
  action: string;
  question_set_id?: number;
  past_year_paper_id?: number;
  details?: string;
  created_at: string;
}

export interface QuestionClient {
  id: number;
  test_id?: number;
  past_year_paper_id?: number;
  question_group_id: number;
  language: string;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  question_order: number;
}

export interface QuestionFull {
  id: number;
  test_id?: number;
  question_set_id?: number;
  past_year_paper_id?: number;
  question_group_id: number;
  language: string;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  correct_option: string;
  explanation?: string;
  question_order: number;
  source: string;
  question_source?: string; // ORIGINAL, AI_GENERATED, AI_TRANSLATED, MANUAL
  status: string;
  created_at: string;
}

export interface Payment {
  id: number;
  user_id: number;
  test_id?: number;
  past_year_paper_id?: number;
  test_title?: string;
  amount: number;
  gateway_order_id?: string;
  gateway_payment_id?: string;
  status: PaymentStatus;
  payment_method: PaymentMethod;
  created_at: string;
  user_email?: string;
  user_name?: string;
}

export interface AttemptEngineData {
  attempt_id: number;
  test_id?: number;
  past_year_paper_id?: number;
  test_title: string;
  exam_name: string;
  duration_minutes: number;
  remaining_seconds: number;
  status: AttemptStatus;
  allowed_languages: string[];
  current_language: string;
  questions: QuestionClient[];
  saved_answers: Record<number, string>; // question_group_id -> selected_option
}

export interface QuestionReview {
  question_group_id: number;
  question_order: number;
  language: string;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  student_answer?: string;
  correct_answer: string;
  status: 'Correct' | 'Incorrect' | 'Not Answered' | string;
  explanation?: string;
}

export interface ResultData {
  attempt_id: number;
  test_id?: number;
  past_year_paper_id?: number;
  test_title: string;
  exam_name: string;
  allowed_languages: string[];
  active_language: string;
  started_at: string;
  submitted_at?: string;
  score: number;
  percentage: number;
  correct_answers: number;
  wrong_answers: number;
  unanswered: number;
  total_questions: number;
  time_taken?: string;
  questions_review: QuestionReview[];
}

export interface AttemptSummary {
  attempt_id: number;
  test_id?: number;
  past_year_paper_id?: number;
  test_title: string;
  exam_name: string;
  submitted_at?: string;
  score: number;
  total_questions: number;
  percentage: number;
  time_taken?: string;
}

export interface AdminStats {
  total_students: number;
  total_exams: number;
  tests_published: number;
  total_attempts: number;
  completed_tests: number;
  total_revenue: number;
  today_attempts: number;
  active_question_sets?: number;
  scheduled_question_sets?: number;
}

