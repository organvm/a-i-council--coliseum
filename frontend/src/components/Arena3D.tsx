'use client';

import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame, useLoader } from '@react-three/fiber';
import { OrbitControls, Text } from '@react-three/drei';
import * as THREE from 'three';
import { useColiseumStore } from '@/lib/store';

function AgentAvatar({ position, name, isAttacking, portraitUrl, role }: any) {
  const mesh = useRef<THREE.Mesh>(null!);
  
  // Load texture if portraitUrl is available
  const texture = portraitUrl ? useLoader(THREE.TextureLoader, portraitUrl) : null;

  useFrame((state, delta) => {
    if (isAttacking && mesh.current) {
      mesh.current.rotation.x += delta * 10;
    } else if (mesh.current) {
      mesh.current.rotation.x = 0;
      mesh.current.rotation.y += delta * 0.5;
    }
  });

  const material = useMemo(() => {
    if (texture) {
      return <meshStandardMaterial map={texture} />;
    }
    const color = role === 'moderator' ? '#ef4444' : role === 'debater' ? '#3b82f6' : '#10b981';
    return <meshStandardMaterial color={color} />;
  }, [texture, role]);

  return (
    <group position={position}>
      <mesh ref={mesh}>
        <boxGeometry args={[1.2, 1.2, 1.2]} />
        {material}
      </mesh>
      <Text
        position={[0, 1.8, 0]}
        fontSize={0.4}
        color="white"
        anchorX="center"
        anchorY="middle"
        font="/fonts/Geist-Black.ttf"
      >
        {name}
      </Text>
    </group>
  );
}

function ArenaFloor() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1, 0]}>
      <planeGeometry args={[30, 30]} />
      <meshStandardMaterial color="#0a0a0a" roughness={0.1} metalness={0.8} />
      <gridHelper args={[30, 30, 0xff0000, 0x222222]} rotation={[-Math.PI / 2, 0, 0]} />
    </mesh>
  );
}

export const Arena3D: React.FC = () => {
  const agents = useColiseumStore((state) => state.agents);

  return (
    <div className="w-full h-96 bg-black rounded-lg border border-gray-800 overflow-hidden relative">
      <Canvas camera={{ position: [0, 8, 12], fov: 40 }}>
        <ambientLight intensity={0.4} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        <spotLight position={[-10, 10, 10]} angle={0.15} penumbra={1} intensity={2} color="#ff0000" />
        
        <ArenaFloor />
        
        {agents.map((agent, index) => (
          <AgentAvatar 
            key={agent.agent_id}
            position={[(index - (agents.length - 1) / 2) * 4, 0, 0]}
            name={agent.name}
            role={agent.role}
            portraitUrl={agent.state?.memory?.portrait_url}
            isAttacking={false}
          />
        ))}
        
        <OrbitControls autoRotate autoRotateSpeed={0.3} maxPolarAngle={Math.PI / 2.1} />
      </Canvas>
      
      <div className="absolute top-4 left-4 flex flex-col gap-1">
        <div className="px-2 py-1 bg-red-600 text-[10px] font-black uppercase text-white rounded">
          GENERATIVE RENDER: ACTIVE
        </div>
        <div className="px-2 py-1 bg-black/50 text-[8px] font-mono text-gray-400 rounded border border-gray-800">
          Uptime: {Math.floor(Date.now() / 1000) % 10000}s
        </div>
      </div>
    </div>
  );
};
