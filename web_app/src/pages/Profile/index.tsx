import { useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { User, Camera, Save, Activity, CalendarDays, Ruler, Mail, ShieldCheck, Clock3 } from 'lucide-react';
import { Card, CardBody, CardHeader, Button, Input, Select, Badge, useToast } from '../../components/ui';
import { PageContainer } from '../../components/layout';
import { userApi } from '../../api/user';
import { uploadApi } from '../../api/upload';

export default function ProfilePage() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data: profile, isLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: () => userApi.getProfile(),
  });

  const updateMutation = useMutation({
    mutationFn: (data: any) => userApi.updateProfile(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      toast.success('Cập nhật hồ sơ thành công');
    },
    onError: () => {
      toast.error('Cập nhật thất bại');
    },
  });

  const uploadAvatarMutation = useMutation({
    mutationFn: (file: File) => uploadApi.uploadProfileImage(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      toast.success('Cập nhật ảnh đại diện thành công');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Tải ảnh thất bại');
    },
  });

  const handleAvatarSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = '';

    if (!file) return;
    if (!file.type.startsWith('image/')) {
      toast.error('Vui lòng chọn file ảnh');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      toast.error('Ảnh không được vượt quá 10MB');
      return;
    }

    uploadAvatarMutation.mutate(file);
  };

  const profileImageSrc = profile?.profile_image_url
    ? profile.profile_image_url.startsWith('http')
      ? profile.profile_image_url
      : `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${profile.profile_image_url}`
    : null;

  const [formData, setFormData] = useState({
    full_name: '',
    date_of_birth: '',
    gender: '',
    height_cm: '',
    activity_level: '',
  });

  useEffect(() => {
    if (!profile) return;

    setFormData({
      full_name: profile.full_name || '',
      date_of_birth: profile.date_of_birth || '',
      gender: profile.gender || '',
      height_cm: profile.height_cm ? String(profile.height_cm) : '',
      activity_level: profile.activity_level || '',
    });
  }, [profile]);

  if (isLoading) {
    return (
      <PageContainer title="Hồ sơ cá nhân" subtitle="Đang tải thông tin của bạn">
        <div className="max-w-3xl mx-auto space-y-6 animate-pulse">
          <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
            <div className="h-20 rounded-2xl bg-gray-100" />
            <div className="-mt-10 flex items-end gap-4">
              <div className="h-24 w-24 rounded-3xl bg-gray-100 border-4 border-white" />
              <div className="space-y-3 pb-2">
                <div className="h-6 w-48 rounded bg-gray-100" />
                <div className="h-4 w-40 rounded bg-gray-100" />
              </div>
            </div>
          </div>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1.3fr_0.9fr]">
            <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm space-y-4">
              <div className="h-5 w-32 rounded bg-gray-100" />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="h-12 rounded-xl bg-gray-100" />
                <div className="h-12 rounded-xl bg-gray-100" />
                <div className="h-12 rounded-xl bg-gray-100" />
                <div className="h-12 rounded-xl bg-gray-100" />
              </div>
              <div className="h-11 w-36 rounded-xl bg-gray-100" />
            </div>
            <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm space-y-4">
              <div className="h-5 w-32 rounded bg-gray-100" />
              <div className="h-16 rounded-2xl bg-gray-100" />
              <div className="h-16 rounded-2xl bg-gray-100" />
              <div className="h-16 rounded-2xl bg-gray-100" />
            </div>
          </div>
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer title="Hồ sơ cá nhân" subtitle="Quản lý thông tin cá nhân của bạn">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Avatar Section */}
        <Card className="overflow-hidden">
          <div className="h-20 bg-gradient-to-r from-primary/10 via-emerald-100/70 to-primary/5" />
          <CardBody className="-mt-10 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div className="flex items-center gap-5">
              <div className="relative">
                <div className="w-24 h-24 bg-white border-4 border-white rounded-3xl shadow-md flex items-center justify-center overflow-hidden">
                  {profileImageSrc ? (
                    <img src={profileImageSrc} alt="Ảnh đại diện" className="w-full h-full rounded-2xl object-cover" />
                  ) : (
                    <div className="w-full h-full bg-primary/10 rounded-2xl flex items-center justify-center">
                      <User className="w-11 h-11 text-primary" />
                    </div>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploadAvatarMutation.isPending}
                  className="absolute -bottom-1 -right-1 p-2 bg-primary text-white rounded-xl hover:bg-primary/90 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Camera className="w-4 h-4" />
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleAvatarSelect}
                />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900">{profile?.full_name || 'Người dùng'}</h2>
                <p className="text-gray-500">{profile?.email}</p>
                {profile?.bmi && (
                  <p className="text-sm text-gray-600 mt-1">
                    BMI: {profile.bmi.toFixed(1)} ({profile.bmi_category})
                  </p>
                )}
              </div>
            </div>
            <Badge variant={profile?.email_verified ? 'success' : 'warning'}>
              {profile?.email_verified ? 'Email đã xác minh' : 'Email chưa xác minh'}
            </Badge>
          </CardBody>
        </Card>

        {/* Personal Info */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <div>
                <h2 className="font-semibold text-gray-900">Thông tin cá nhân</h2>
                <p className="text-sm text-gray-500 mt-1">Cập nhật thông tin để cá nhân hóa kế hoạch dinh dưỡng.</p>
              </div>
              <Badge variant="info">Hồ sơ cơ bản</Badge>
            </div>
          </CardHeader>
          <CardBody className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Họ và tên"
                value={profile?.full_name || ''}
                disabled
              />
              <Input
                label="Email"
                value={profile?.email || ''}
                disabled
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Ngày sinh"
                type="date"
                value={formData.date_of_birth}
                onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
              />
              <Select
                label="Giới tính"
                value={formData.gender}
                onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                options={[
                  { value: 'male', label: 'Nam' },
                  { value: 'female', label: 'Nữ' },
                  { value: 'other', label: 'Khác' },
                ]}
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Chiều cao (cm)"
                type="number"
                value={formData.height_cm || ''}
                onChange={(e) => setFormData({ ...formData, height_cm: e.target.value })}
                placeholder="170"
              />
              <Select
                label="Mức độ hoạt động"
                value={formData.activity_level}
                onChange={(e) => setFormData({ ...formData, activity_level: e.target.value })}
                options={[
                  { value: 'sedentary', label: 'Ít vận động' },
                  { value: 'lightly_active', label: 'Vận động nhẹ' },
                  { value: 'moderately_active', label: 'Vận động vừa' },
                  { value: 'very_active', label: 'Vận động nhiều' },
                  { value: 'extra_active', label: 'Vận động rất nhiều' },
                ]}
              />
            </div>
            <div className="pt-2">
              <Button
                onClick={() => updateMutation.mutate(formData)}
                isLoading={updateMutation.isPending}
                leftIcon={<Save className="w-4 h-4" />}
                className="min-w-[180px]"
              >
                Lưu thay đổi
              </Button>
            </div>
          </CardBody>
        </Card>

        {/* Health Metrics */}
        {profile?.bmi && (
          <Card>
            <CardHeader>
              <h2 className="font-semibold text-gray-900">Chỉ số sức khỏe</h2>
            </CardHeader>
            <CardBody>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <HealthMetric
                  label="BMI"
                  value={profile.bmi.toFixed(1)}
                  note={profile.bmi_category || '---'}
                  icon={<Activity className="w-4 h-4" />}
                />
                {profile.age && (
                  <HealthMetric
                    label="Tuổi"
                    value={`${profile.age}`}
                    note="tuổi"
                    icon={<CalendarDays className="w-4 h-4" />}
                  />
                )}
                {profile.height_cm && (
                  <HealthMetric
                    label="Chiều cao"
                    value={`${profile.height_cm}`}
                    note="cm"
                    icon={<Ruler className="w-4 h-4" />}
                  />
                )}
              </div>
            </CardBody>
          </Card>
        )}

        {/* Account Info */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <h2 className="font-semibold text-gray-900">Thông tin tài khoản</h2>
              <Badge variant={profile?.email_verified ? 'success' : 'warning'}>
                {profile?.email_verified ? 'Đã xác minh' : 'Chưa xác minh'}
              </Badge>
            </div>
          </CardHeader>
          <CardBody className="space-y-3">
            <InfoRow
              icon={<Mail className="w-4 h-4" />}
              label="Email"
              value={profile?.email || '-'}
            />
            <InfoRow
              icon={<Clock3 className="w-4 h-4" />}
              label="Ngày tham gia"
              value={profile?.created_at ? new Date(profile.created_at).toLocaleDateString('vi-VN') : '-'}
            />
            <InfoRow
              icon={<CalendarDays className="w-4 h-4" />}
              label="Đăng nhập cuối"
              value={profile?.last_login ? new Date(profile.last_login).toLocaleDateString('vi-VN') : '-'}
            />
            <InfoRow
              icon={<ShieldCheck className="w-4 h-4" />}
              label="Xác minh email"
              value={profile?.email_verified ? 'Đã xác minh' : 'Chưa xác minh'}
              valueClassName={profile?.email_verified ? 'text-green-600' : 'text-red-600'}
            />
          </CardBody>
        </Card>
      </div>
    </PageContainer>
  );
}

function HealthMetric({ label, value, note, icon }: { label: string; value: string; note: string; icon: ReactNode }) {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm text-gray-500">{label}</p>
        <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary/10 text-primary">{icon}</span>
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{note}</p>
    </div>
  );
}

function InfoRow({
  icon,
  label,
  value,
  valueClassName = 'text-gray-900',
}: {
  icon: ReactNode;
  label: string;
  value: string;
  valueClassName?: string;
}) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-2xl border border-gray-100 bg-gray-50/80 px-4 py-3">
      <div className="flex min-w-0 items-center gap-3">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-primary shadow-sm">
          {icon}
        </span>
        <span className="text-sm text-gray-500">{label}</span>
      </div>
      <span className={`text-sm font-medium text-right ${valueClassName}`}>{value}</span>
    </div>
  );
}