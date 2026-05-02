import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { Mail, Lock, Leaf, Eye, EyeOff } from 'lucide-react';
import { Button, Input, Card, CardBody, Checkbox, Badge } from '../../components/ui';
import { useAuthStore } from '../../stores/authStore';
import { isOnboardingPending } from '../../lib/onboardingStorage';

interface LoginFormData {
  email: string;
  password: string;
}

export default function LoginPage() {
  const navigate = useNavigate();
  const { login, isSubmitting } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>();

  const onSubmit = async (data: LoginFormData) => {
    try {
      setError('');
      await login(data.email, data.password);
      // Sau khi login thành công, lấy thông tin user từ store để xác định redirect
      const storedUser = useAuthStore.getState().user;
      if (storedUser?.is_admin) {
        navigate('/admin/dashboard', { replace: true });
      } else if (isOnboardingPending()) {
        navigate('/onboarding', { replace: true });
      } else {
        navigate('/dashboard', { replace: true });
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const message =
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join('; ') || 'Email hoặc mật khẩu không đúng'
            : 'Email hoặc mật khẩu không đúng';
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
            Ăn uống thông minh mỗi ngày
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Chào mừng bạn quay lại</h1>
          <p className="text-gray-500 mt-2">Đăng nhập để tiếp tục với NutriAI</p>
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

              <div className="relative">
                <Input
                  label="Mật khẩu"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Nhập mật khẩu"
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
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-[38px] rounded-lg p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>

              <div className="flex items-start justify-between gap-4">
                <Checkbox label="Ghi nhớ đăng nhập" className="mt-0.5" />
                <Link to="/forgot-password" className="text-sm font-medium text-primary hover:underline">
                  Quên mật khẩu?
                </Link>
              </div>

              <Button type="submit" className="w-full" isLoading={isSubmitting}>
                Đăng nhập
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-sm text-gray-600">
                Chưa có tài khoản?{' '}
                <Link to="/register" className="text-primary font-medium hover:underline">
                  Đăng ký ngay
                </Link>
              </p>
            </div>
          </CardBody>
        </Card>

        {/* Demo credentials */}
        <div className="mt-4 rounded-2xl border border-emerald-100 bg-white/80 p-4 shadow-sm backdrop-blur">
          <div className="mb-2 flex justify-center">
            <Badge variant="success">Demo admin</Badge>
          </div>
          <p className="text-sm text-gray-600 text-center">
            Tài khoản Admin: <span className="font-mono text-gray-800">admin@nutriai.vn / Admin123</span>
          </p>
        </div>
      </div>
    </div>
  );
}