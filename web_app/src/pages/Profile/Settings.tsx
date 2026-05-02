import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Settings, User, Bell, Shield, Save } from 'lucide-react';
import { Card, CardBody, CardHeader, Button, Input, Select, Switch, useToast } from '../../components/ui';
import { PageContainer } from '../../components/layout';
import { authApi } from '../../api/auth';
import { userApi } from '../../api/user';

export default function SettingsPage() {
  const toast = useToast();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: profile } = useQuery({
    queryKey: ['profile'],
    queryFn: () => userApi.getProfile(),
  });

  // General settings
  const [generalSettings, setGeneralSettings] = useState({
    language: 'vi',
    timezone: 'Asia/Ho_Chi_Minh',
    theme: 'light',
  });

  // Notification settings
  const [notifications, setNotifications] = useState(() => {
    const stored = localStorage.getItem('nutriai_notifications');
    if (!stored) {
      return {
        email_reminders: true,
        meal_reminders: true,
        goal_progress: true,
        weekly_summary: false,
      };
    }

    try {
      return JSON.parse(stored);
    } catch {
      return {
        email_reminders: true,
        meal_reminders: true,
        goal_progress: true,
        weekly_summary: false,
      };
    }
  });

  // Privacy settings
  const [privacy, setPrivacy] = useState({
    show_weight: true,
    show_meals: true,
  });

  // Password change
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  const saveGeneralMutation = useMutation({
    mutationFn: () =>
      userApi.updateProfile({
        language: generalSettings.language,
        timezone: generalSettings.timezone,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      localStorage.setItem('nutriai_theme', generalSettings.theme);
      toast.success('Đã lưu cài đặt chung');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Lưu cài đặt thất bại');
    },
  });

  useEffect(() => {
    if (!profile) return;

    setGeneralSettings((prev) => ({
      ...prev,
      language: profile.language || 'vi',
      timezone: profile.timezone || 'Asia/Ho_Chi_Minh',
    }));
  }, [profile]);

  useEffect(() => {
    const storedTheme = localStorage.getItem('nutriai_theme');
    if (!storedTheme) return;

    setGeneralSettings((prev) => ({ ...prev, theme: storedTheme }));
  }, []);

  const handlePasswordChange = async () => {
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      toast.error('Mật khẩu mới không khớp');
      return;
    }
    if (passwordForm.new_password.length < 6) {
      toast.error('Mật khẩu mới phải có ít nhất 6 ký tự');
      return;
    }

    try {
      const response = await authApi.changePassword({
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
      });

      toast.success(response.message || 'Đổi mật khẩu thành công');
      setPasswordForm({ current_password: '', new_password: '', confirm_password: '' });
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Đổi mật khẩu thất bại');
    }
  };

  const handleSaveGeneral = () => {
    saveGeneralMutation.mutate();
  };

  const handleSaveNotifications = () => {
    localStorage.setItem('nutriai_notifications', JSON.stringify(notifications));
    toast.success('Đã lưu cài đặt thông báo');
  };

  const scrollToPasswordSection = () => {
    document.getElementById('password-section')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <PageContainer
      title="Cài đặt"
      subtitle="Quản lý cài đặt tài khoản và ứng dụng"
    >
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Profile Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-50 rounded-lg">
                <User className="w-5 h-5 text-blue-500" />
              </div>
              <h2 className="font-semibold text-gray-900">Tài khoản</h2>
            </div>
          </CardHeader>
          <CardBody className="space-y-4">
            <Button variant="outline" className="w-full justify-start" onClick={() => navigate('/profile')}>
              <User className="w-4 h-4 mr-3" />
              Chỉnh sửa hồ sơ
            </Button>
            <Button variant="outline" className="w-full justify-start" onClick={scrollToPasswordSection}>
              <Shield className="w-4 h-4 mr-3" />
              Đổi mật khẩu
            </Button>
          </CardBody>
        </Card>

        {/* Password Change */}
        <div id="password-section" className="scroll-mt-24">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-red-50 rounded-lg">
                  <Shield className="w-5 h-5 text-red-500" />
                </div>
                <h2 className="font-semibold text-gray-900">Đổi mật khẩu</h2>
              </div>
            </CardHeader>
            <CardBody className="space-y-4">
            <Input
              label="Mật khẩu hiện tại"
              type="password"
              value={passwordForm.current_password}
              onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
            />
            <Input
              label="Mật khẩu mới"
              type="password"
              value={passwordForm.new_password}
              onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
              helperText="Ít nhất 6 ký tự"
            />
            <Input
              label="Xác nhận mật khẩu mới"
              type="password"
              value={passwordForm.confirm_password}
              onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
            />
            <Button onClick={handlePasswordChange} leftIcon={<Save className="w-4 h-4" />}>
              Cập nhật mật khẩu
            </Button>
            </CardBody>
          </Card>
        </div>

        {/* General Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-50 rounded-lg">
                <Settings className="w-5 h-5 text-purple-500" />
              </div>
              <h2 className="font-semibold text-gray-900">Cài đặt chung</h2>
            </div>
          </CardHeader>
          <CardBody className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Select
                label="Ngôn ngữ"
                value={generalSettings.language}
                onChange={(e) => setGeneralSettings({ ...generalSettings, language: e.target.value })}
                options={[
                  { value: 'vi', label: 'Tiếng Việt' },
                  { value: 'en', label: 'English' },
                ]}
              />
              <Select
                label="Múi giờ"
                value={generalSettings.timezone}
                onChange={(e) => setGeneralSettings({ ...generalSettings, timezone: e.target.value })}
                options={[
                  { value: 'Asia/Ho_Chi_Minh', label: 'Việt Nam (UTC+7)' },
                  { value: 'Asia/Bangkok', label: 'Thái Lan (UTC+7)' },
                  { value: 'Asia/Singapore', label: 'Singapore (UTC+8)' },
                ]}
              />
            </div>
            <Select
              label="Giao diện"
              value={generalSettings.theme}
              onChange={(e) => setGeneralSettings({ ...generalSettings, theme: e.target.value })}
              options={[
                { value: 'light', label: 'Sáng' },
                { value: 'dark', label: 'Tối' },
                { value: 'system', label: 'Theo hệ thống' },
              ]}
            />
            <Button
              variant="outline"
              onClick={handleSaveGeneral}
              isLoading={saveGeneralMutation.isPending}
              leftIcon={<Save className="w-4 h-4" />}
            >
              Lưu cài đặt
            </Button>
          </CardBody>
        </Card>

        {/* Notification Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-50 rounded-lg">
                <Bell className="w-5 h-5 text-yellow-500" />
              </div>
              <h2 className="font-semibold text-gray-900">Thông báo</h2>
            </div>
          </CardHeader>
          <CardBody className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Nhắc nhở bữa ăn</p>
                <p className="text-sm text-gray-500">Nhận thông báo khi đến giờ ăn</p>
              </div>
              <Switch
                checked={notifications.meal_reminders}
                onChange={(e) => setNotifications({ ...notifications, meal_reminders: e.target.checked })}
              />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Tiến độ mục tiêu</p>
                <p className="text-sm text-gray-500">Thông báo khi đạt được mục tiêu</p>
              </div>
              <Switch
                checked={notifications.goal_progress}
                onChange={(e) => setNotifications({ ...notifications, goal_progress: e.target.checked })}
              />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Email reminders</p>
                <p className="text-sm text-gray-500">Nhận email nhắc nhở</p>
              </div>
              <Switch
                checked={notifications.email_reminders}
                onChange={(e) => setNotifications({ ...notifications, email_reminders: e.target.checked })}
              />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Tóm tắt hàng tuần</p>
                <p className="text-sm text-gray-500">Nhận email tổng kết tuần</p>
              </div>
              <Switch
                checked={notifications.weekly_summary}
                onChange={(e) => setNotifications({ ...notifications, weekly_summary: e.target.checked })}
              />
            </div>
            <Button variant="outline" onClick={handleSaveNotifications} leftIcon={<Save className="w-4 h-4" />}>
              Lưu cài đặt thông báo
            </Button>
          </CardBody>
        </Card>

        {/* Privacy */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-50 rounded-lg">
                <Shield className="w-5 h-5 text-green-500" />
              </div>
              <h2 className="font-semibold text-gray-900">Quyền riêng tư</h2>
            </div>
          </CardHeader>
          <CardBody className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Hiển thị cân nặng</p>
                <p className="text-sm text-gray-500">Cho phép người khác thấy cân nặng của bạn</p>
              </div>
              <Switch
                checked={privacy.show_weight}
                onChange={(e) => setPrivacy({ ...privacy, show_weight: e.target.checked })}
              />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Hiển thị bữa ăn</p>
                <p className="text-sm text-gray-500">Cho phép người khác thấy nhật ký ăn của bạn</p>
              </div>
              <Switch
                checked={privacy.show_meals}
                onChange={(e) => setPrivacy({ ...privacy, show_meals: e.target.checked })}
              />
            </div>
          </CardBody>
        </Card>

        {/* Danger Zone */}
        <Card className="border-red-200">
          <CardHeader className="bg-red-50/50">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-lg">
                <Shield className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <h2 className="font-semibold text-red-900">Vùng nguy hiểm</h2>
                <p className="text-sm text-red-600">Các hành động không thể hoàn tác</p>
              </div>
            </div>
          </CardHeader>
          <CardBody className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Xóa tài khoản</p>
                <p className="text-sm text-gray-500">Xóa vĩnh viễn tài khoản và tất cả dữ liệu</p>
              </div>
              <Button variant="danger" size="sm">
                Xóa tài khoản
              </Button>
            </div>
          </CardBody>
        </Card>
      </div>
    </PageContainer>
  );
}