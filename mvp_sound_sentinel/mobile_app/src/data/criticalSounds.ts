// Критические и опасные звуки для уведомлений
export const CRITICAL_SOUNDS = [
  // Опасные для жизни
  'Fire',
  'Smoke alarm',
  'Fire alarm',
  'Burglar alarm',
  'Car alarm',
  'Siren',
  'Emergency vehicle',
  'Police car (siren)',
  'Ambulance (siren)',
  'Fire engine',
  
  // Вода и затопление
  'Water',
  'Running water',
  'Dripping tap',
  'Faucet',
  'Shower',
  'Bath',
  'Splash',
  'Gurgling',
  
  // Дети и безопасность
  'Crying baby',
  'Baby cry',
  'Infant cry',
  'Child speech',
  'Screaming',
  'Shout',
  'Yell',
  
  // Взлом и безопасность
  'Glass break',
  'Window shatter',
  'Door slam',
  'Knock',
  'Bang',
  'Crash',
  'Impact',
  
  // Электричество и приборы
  'Power tool',
  'Drill',
  'Saw',
  'Electric shaver',
  'Hair dryer',
  'Vacuum cleaner',
  'Blender',
  
  // Животные (опасные)
  'Dog bark',
  'Dog growl',
  'Cat meow',
  'Insect buzz',
  'Bee',
  'Wasp',
  'Hiss',
  
  // Природные явления
  'Thunder',
  'Wind',
  'Storm',
  'Rain',
  'Hail',
  'Explosion',
  'Gunshot',
  'Fireworks',
];

// Бытовые звуки (не критичные, но важные)
export const HOUSEHOLD_SOUNDS = [
  'Doorbell',
  'Telephone bell ringing',
  'Alarm clock',
  'Timer',
  'Microwave oven',
  'Dishwasher',
  'Washing machine',
  'Dryer',
  'Refrigerator',
  'Computer keyboard',
  'Typing',
  'Mouse click',
  'Printer',
  'Scanner',
];

// Функция проверки критичности звука
export const isCriticalSound = (soundType: string): boolean => {
  return CRITICAL_SOUNDS.some(critical => 
    soundType.toLowerCase().includes(critical.toLowerCase()) ||
    critical.toLowerCase().includes(soundType.toLowerCase())
  );
};

// Функция проверки важного звука
export const isImportantSound = (soundType: string): boolean => {
  return HOUSEHOLD_SOUNDS.some(household => 
    soundType.toLowerCase().includes(household.toLowerCase()) ||
    household.toLowerCase().includes(soundType.toLowerCase())
  );
};

// Получение иконки для звука
export const getSoundIcon = (soundType: string): string => {
  const lowerSound = soundType.toLowerCase();
  
  if (lowerSound.includes('fire') || lowerSound.includes('alarm')) {
    return '🔥';
  }
  if (lowerSound.includes('water') || lowerSound.includes('drip')) {
    return '💧';
  }
  if (lowerSound.includes('baby') || lowerSound.includes('cry')) {
    return '👶';
  }
  if (lowerSound.includes('siren') || lowerSound.includes('police')) {
    return '🚨';
  }
  if (lowerSound.includes('glass') || lowerSound.includes('break')) {
    return '💥';
  }
  if (lowerSound.includes('dog') || lowerSound.includes('bark')) {
    return '🐕';
  }
  if (lowerSound.includes('doorbell') || lowerSound.includes('knock')) {
    return '🔔';
  }
  if (lowerSound.includes('telephone') || lowerSound.includes('ring')) {
    return '📞';
  }
  if (lowerSound.includes('thunder') || lowerSound.includes('storm')) {
    return '⛈️';
  }
  if (lowerSound.includes('power tool') || lowerSound.includes('drill')) {
    return '🔧';
  }
  
  return '🔊';
};
