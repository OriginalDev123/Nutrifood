
interface LineChartProps {
  data: { label: string; value: number }[];
  height?: number;
  color?: string;
  showDot?: boolean;
  fill?: boolean;
}

export function LineChart({ data, height = 200, color = '#22C55E', showDot = false, fill = false }: LineChartProps) {
  if (!data || data.length === 0) {
    return <div style={{ height }} className="flex items-center justify-center text-gray-400 text-sm">Không có dữ liệu</div>;
  }

  const allValues = data.map(d => d.value);
  const maxValue = Math.max(...allValues, 1);
  const minValue = Math.min(...allValues, 0);
  const range = maxValue - minValue || 1;
  const barCount = data.length;
  const w = 600;
  const h = height * 2;
  const padX = 40;
  const padY = 20;
  const chartW = w - padX * 2;
  const chartH = h - padY * 2;

  const xAt = (i: number) => padX + (barCount <= 1 ? chartW / 2 : (i / (barCount - 1)) * chartW);
  const yAt = (v: number) => padY + chartH - ((v - minValue) / range) * chartH;

  const points = data.map((d, i) => `${xAt(i)},${yAt(d.value)}`).join(' ');
  const areaPath = data.length > 0
    ? `M ${xAt(0)} ${padY + chartH} L ${points.replace(/,/g, ' L ')} L ${xAt(data.length - 1)} ${padY + chartH} Z`
    : '';

  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="none"
      style={{ width: '100%', height: `${height}px` }}
      className="overflow-visible"
    >
      {fill && (
        <path
          d={areaPath}
          fill={color}
          fillOpacity={0.12}
        />
      )}
      <path
        d={`M ${points.replace(/,/g, ' L ')}`}
        fill="none"
        stroke={color}
        strokeWidth={4}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      {showDot && data.map((d, i) => (
        <circle
          key={i}
          cx={xAt(i)}
          cy={yAt(d.value)}
          r={5}
          fill={color}
          stroke="#fff"
          strokeWidth={2}
        />
      ))}
    </svg>
  );
}

interface BarChartProps {
  data: { label: string; value: number; color?: string }[];
  height?: number;
  maxValue?: number;
}

export function BarChart({ data, height = 200, maxValue: providedMax }: BarChartProps) {
  const max = providedMax || Math.max(...data.map(d => d.value), 1);

  return (
    <div className="flex items-end gap-2" style={{ height: `${height}px` }}>
      {data.map((d, i) => (
        <div key={i} className="flex-1 flex flex-col items-center gap-1">
          <div className="w-full flex flex-col justify-end" style={{ height: `${height - 40}px` }}>
            <div
              className="w-full rounded-t-md transition-all duration-300"
              style={{
                height: `${(d.value / max) * 100}%`,
                backgroundColor: d.color || '#22C55E',
              }}
            />
          </div>
          <span className="text-xs text-gray-500 truncate w-full text-center">{d.label}</span>
        </div>
      ))}
    </div>
  );
}

interface DonutChartProps {
  data: { label: string; value: number; color: string }[];
  size?: number;
  strokeWidth?: number;
  showLegend?: boolean;
}

export function DonutChart({ data, size = 120, strokeWidth = 20, showLegend = true }: DonutChartProps) {
  const total = data.reduce((sum, d) => sum + d.value, 0);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  let offset = 0;

  return (
    <div className="flex items-center gap-6">
      <div className="relative" style={{ width: size, height: size }}>
        <svg viewBox={`0 0 ${size} ${size}`} className="-rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#f3f4f6"
            strokeWidth={strokeWidth}
          />
          {data.map((d, i) => {
            const percentage = d.value / total;
            const dashLength = circumference * percentage;
            const dashOffset = -offset * circumference;
            offset += percentage;

            return (
              <circle
                key={i}
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="none"
                stroke={d.color}
                strokeWidth={strokeWidth}
                strokeDasharray={`${dashLength} ${circumference - dashLength}`}
                strokeDashoffset={dashOffset}
                className="transition-all duration-500"
              />
            );
          })}
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-lg font-bold text-gray-900">{total}</span>
        </div>
      </div>
      {showLegend && (
        <div className="space-y-2">
          {data.map((d, i) => (
            <div key={i} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: d.color }}
              />
              <span className="text-sm text-gray-600">{d.label}</span>
              <span className="text-sm font-medium text-gray-900">
                {d.value}g ({Math.round((d.value / total) * 100)}%)
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

interface AreaChartProps {
  data: { label: string; value: number }[];
  height?: number;
  color?: string;
  secondaryData?: { label: string; value: number }[];
  secondaryColor?: string;
  showDot?: boolean;
}

export function AreaChart({
  data,
  height = 200,
  color = '#22C55E',
  secondaryData,
  secondaryColor = '#3B82F6',
  showDot = false,
}: AreaChartProps) {
  if (!data || data.length === 0) {
    return <div style={{ height }} className="flex items-center justify-center text-gray-400 text-sm">Không có dữ liệu</div>;
  }

  const allValues = [
    ...data.map(d => d.value),
    ...(secondaryData?.map(d => d.value) || []),
  ];
  const maxValue = Math.max(...allValues, 1);
  const minValue = Math.min(...allValues, 0);
  const range = maxValue - minValue || 1;
  const pointCount = data.length;
  const w = 600;
  const h = height * 2;
  const padX = 20;
  const padY = 20;
  const chartW = w - padX * 2;
  const chartH = h - padY * 2;

  const xAt = (i: number) => padX + (pointCount <= 1 ? chartW / 2 : (i / (pointCount - 1)) * chartW);
  const yAt = (v: number) => padY + chartH - ((v - minValue) / range) * chartH;

  const dataPath = data.map((d, i) => `${i === 0 ? 'M' : 'L'} ${xAt(i)} ${yAt(d.value)}`).join(' ');
  const dataArea = `${dataPath} L ${xAt(data.length - 1)} ${padY + chartH} L ${xAt(0)} ${padY + chartH} Z`;

  const secondaryPath = secondaryData && secondaryData.length > 0
    ? secondaryData.map((d, i) => `${i === 0 ? 'M' : 'L'} ${xAt(i)} ${yAt(d.value)}`).join(' ')
    : '';

  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="none"
      style={{ width: '100%', height: `${height}px` }}
      className="overflow-visible"
    >
      {/* Grid lines */}
      {[0, 0.25, 0.5, 0.75, 1].map((frac, i) => (
        <line
          key={i}
          x1={padX}
          y1={padY + chartH * frac}
          x2={w - padX}
          y2={padY + chartH * frac}
          stroke="#e5e7eb"
          strokeWidth={1}
        />
      ))}

      {/* Secondary data line (target) */}
      {secondaryPath && (
        <>
          <path
            d={secondaryPath}
            fill="none"
            stroke={secondaryColor}
            strokeWidth={3}
            strokeDasharray="8 4"
            strokeOpacity={0.7}
          />
        </>
      )}

      {/* Area fill */}
      <path
        d={dataArea}
        fill={color}
        fillOpacity={0.15}
      />

      {/* Main line */}
      <path
        d={dataPath}
        fill="none"
        stroke={color}
        strokeWidth={3.5}
        strokeLinejoin="round"
        strokeLinecap="round"
      />

      {/* Dots */}
      {showDot && data.map((d, i) => (
        <circle
          key={i}
          cx={xAt(i)}
          cy={yAt(d.value)}
          r={5}
          fill={color}
          stroke="#fff"
          strokeWidth={2}
        />
      ))}

      {/* X-axis labels */}
      {data.map((d, i) => {
        if (data.length <= 7 || i % Math.ceil(data.length / 7) === 0) {
          return (
            <text
              key={`label-${i}`}
              x={xAt(i)}
              y={padY + chartH + 16}
              textAnchor="middle"
              fontSize={10}
              fill="#9ca3af"
            >
              {d.label}
            </text>
          );
        }
        return null;
      })}

      {/* Y-axis labels */}
      {[0, 0.25, 0.5, 0.75, 1].map((frac, i) => (
        <text
          key={`y-${i}`}
          x={padX - 4}
          y={padY + chartH * frac + 4}
          textAnchor="end"
          fontSize={10}
          fill="#9ca3af"
        >
          {Math.round(maxValue - (maxValue - minValue) * frac)}
        </text>
      ))}
    </svg>
  );
}