'use client';

import React, { useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, useGLTF } from '@react-three/drei';
import * as THREE from 'three';

function AgentAvatar({ position, color, name, isAttacking }: any) {
  const mesh = useRef<THREE.Mesh>(null!);
  
  useFrame((state, delta) => {
    if (isAttacking && mesh.current) {
      mesh.current.rotation.x += delta * 10;
    } else if (mesh.current) {
      mesh.current.rotation.x = 0;
      mesh.current.rotation.y += delta * 0.5;
    }
  });

  return (
    <group position={position}>
      <mesh ref={mesh}>
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial color={color} />
      </mesh>
      <Text
        position={[0, 1.5, 0]}
        fontSize={0.5}
        color="white"
        anchorX="center"
        anchorY="middle"
      >
        {name}
      </Text>
    </group>
  );
}

function ArenaFloor() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1, 0]}>
      <planeGeometry args={[20, 20]} />
      <meshStandardMaterial color="#1a1a1a" />
      <gridHelper args={[20, 20, 0x444444, 0x222222]} rotation={[-Math.PI / 2, 0, 0]} />
    </mesh>
  );
}

export const Arena3D: React.FC = () => {
  return (
    <div className="w-full h-96 bg-black rounded-lg border border-gray-800 overflow-hidden">
      <Canvas camera={{ position: [0, 5, 10], fov: 50 }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />
        
        <ArenaFloor />
        
        <AgentAvatar position={[-3, 0, 0]} color="#ef4444" name="Atlas" isAttacking={false} />
        <AgentAvatar position={[3, 0, 0]} color="#3b82f6" name="Socrates" isAttacking={false} />
        
        <OrbitControls autoRotate autoRotateSpeed={0.5} />
      </Canvas>
      
      <div className="absolute top-4 left-4 px-2 py-1 bg-black/50 text-xs font-mono text-green-500 rounded border border-green-900">
        LIVE RENDER: 60 FPS
      </div>
    </div>
  );
};
