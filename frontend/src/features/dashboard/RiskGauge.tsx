import React from 'react';
import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from 'recharts';

interface RiskGaugeProps {
  risk: number; // A value between 0 and 1
}

const RiskGauge: React.FC<RiskGaugeProps> = ({ risk }) => {
  const riskPercent = Math.round(risk * 100);

  // Determine color based on risk
  const color = riskPercent > 75 ? '#FF4500' : riskPercent > 50 ? '#FFA500' : '#228B22';

  // Recharts needs data in this format
  const data = [
    {
      name: 'Risk',
      value: riskPercent,
      fill: color,
    },
  ];

  return (
    <ResponsiveContainer width="100%" height={200}>
      <RadialBarChart
        innerRadius="70%"
        outerRadius="100%"
        data={data}
        startAngle={180}
        endAngle={0}
        barSize={30}
      >
        <PolarAngleAxis
          type="number"
          domain={[0, 100]}
          angleAxisId={0}
          tick={false}
        />
        <RadialBar
          background
          dataKey="value"
          angleAxisId={0}
          cornerRadius={15}
        />
        {/* Label in the center */}
        <text
          x="50%"
          y="55%"
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize="2.5rem"
          fontWeight="bold"
          fill={color}
        >
          {`${riskPercent}%`}
        </text>
        <text
          x="50%"
          y="70%"
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize="1rem"
          fill="#666"
        >
          Failure Risk
        </text>
      </RadialBarChart>
    </ResponsiveContainer>
  );
};

export default RiskGauge;