import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { Mail, Lock, User, Leaf, Eye, EyeOff } from 'lucide-react';
import { Button, Input, Card, CardBody, Checkbox } from '../../components/ui';
import { useAuthStore } from '../../stores/authStore';
import { authApi } from '../../api/auth';
import { setOnboardingPending } from '../../lib/onboardingStorage';

interface RegisterFormData {
  email: string;
  password: string;
  confirmPassword: string;
  full_name: string;
  terms: boolean;
}

export default function RegisterPage() {
  const navigate = useNavigate();
  const { isSubmitting: _isSubmitting } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterFormData>();

  const password = watch('password');

  const onSubmit = async (data: RegisterFormData) => {
    try {
      setError('');
      setIsRegistering(true);

      // 1. Đăng ký tài khoản
      await authApi.register({ email: data.email, password: data.password, full_name: data.full_name });

      // 2. Đăng nhập ngay để lấy token
      await authApi.login({ email: data.email, password: data.password });

      // 3. Lấy thông tin user
      const user = await authApi.me();

      // 4. Đánh dấu cần onboarding (localStorage)
      setOnboardingPending();

      // 5. Cập nhật store trực tiếp bằng setState để tránh bị fetchUser overwrite
      useAuthStore.setState({ user, isAuthenticated: true, isSubmitting: false });

      // 6. Chuyển hướng sang onboarding — dùng setTimeout(0) để đợi React re-render App.tsx
      //    trước khi OnboardingGate/ProtectedRoute nhìn thấy user mới.
      setTimeout(() => navigate('/onboarding', { replace: true }), 0);
    } catch (err: any) {
      setIsRegistering(false);
      const detail = err.response?.data?.detail;
      const message =
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join('; ') || 'Đăng ký thất bại. Vui lòng thử lại.'
            : 'Đăng ký thất bại. Vui lòng thử lại.';
      setError(message);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-green-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-primary to-emerald-600 rounded-3xl mb-4 shadow-lg shadow-emerald-200/70">
            <Leaf className="w-8 h-8 text-white" />
          </div>
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-100 bg-white/80 px-3 py-1 text-xs font-medium text-primary shadow-sm mb-4">
            Khởi đầu hành trình dinh dưỡng tốt hơn
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Tạo tài khoản</h1>
          <p className="text-gray-500 mt-2">Tham gia NutriAI để bắt đầu hành trình dinh dưỡng</p>
        </div>

        <Card className="border-white/70 bg-white/90 backdrop-blur">
          <CardBody className="p-7">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {error && (
                <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg border border-red-200">
                  {error}
                </div>
              )}

              <Input
                label="Họ và tên"
                type="text"
                placeholder="Nguyễn Văn A"
                leftIcon={<User className="w-5 h-5" />}
                error={errors.full_name?.message}
                {...register('full_name', {
                  required: 'Vui lòng nhập họ tên',
                  minLength: {
                    value: 2,
                    message: 'Họ tên phải có ít nhất 2 ký tự',
                  },
                })}
              />

              <Input
                label="Email"
                type="email"
                placeholder="nguyen@example.com"
                leftIcon={<Mail className="w-5 h-5" />}
                error={errors.email?.message}
                {...register('email', {
                  required: 'Vui lòng nhập email',
                  pattern: {
                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                    message: 'Email không hợp lệ',
                  },
                })}
              />

              <div className="rounded-2xl border border-gray-200 bg-gray-50/70 p-4 space-y-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-gray-900">Thiết lập mật khẩu</p>
                    <p className="text-xs text-gray-500">Mật khẩu cần có ít nhất 6 ký tự.</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="inline-flex items-center gap-2 rounded-full border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-600 hover:border-gray-300 hover:text-gray-800"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    {showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                  </button>
                </div>

                <Input
                  label="Mật khẩu"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Ít nhất 6 ký tự"
                  leftIcon={<Lock className="w-5 h-5" />}
                  error={errors.password?.message}
                  {...register('password', {
                    required: 'Vui lòng nhập mật khẩu',
                    minLength: {
                      value: 6,
                      message: 'Mật khẩu phải có ít nhất 6 ký tự',
                    },
                  })}
                />

                <Input
                  label="Xác nhận mật khẩu"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Nhập lại mật khẩu"
                  leftIcon={<Lock className="w-5 h-5" />}
                  error={errors.confirmPassword?.message}
                  {...register('confirmPassword', {
                    required: 'Vui lòng xác nhận mật khẩu',
                    validate: (value) =>
                      value === password || 'Mật khẩu không khớp',
                  })}
                />
              </div>

              <div className="rounded-2xl border border-gray-200 bg-gray-50/80 p-4">
                <Checkbox
                  id="terms"
                  error={errors.terms?.message}
                  label="Tôi đồng ý với Điều khoản sử dụng và Chính sách bảo mật"
                  className="mt-0.5"
                  {...register('terms', {
                    required: 'Bạn phải đồng ý với điều khoản',
                  })}
                />
              </div>

              <Button type="submit" className="w-full" isLoading={isRegistering}>
                Đăng ký
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-sm text-gray-600">
                Đã có tài khoản?{' '}
                <Link to="/login" className="text-primary font-medium hover:underline">
                  Đăng nhập ngay
                </Link>
              </p>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
