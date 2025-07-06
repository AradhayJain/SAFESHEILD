import AsyncStorage from '@react-native-async-storage/async-storage';

const KEYS = {
  swipeDistances: 'swipeDistances',
  swipeDurations: 'swipeDurations',
  swipeSpeeds: 'swipeSpeeds',
  swipeDirections: 'swipeDirections',
  swipeAccelerations: 'swipeAccelerations',
  holdTimes: 'holdTimes',
  flightTimes: 'flightTimes',
  backspaceRates: 'backspaceRates',
  typingSpeeds: 'typingSpeeds',
};

async function appendToArray(key: string, value: number) {
  try {
    const existing = await AsyncStorage.getItem(key);
    const arr = existing ? JSON.parse(existing) : [];
    arr.push(value);
    await AsyncStorage.setItem(key, JSON.stringify(arr));
  } catch (e) {
    console.error('Error appending to', key, e);
  }
}

export const BehaviourTracker = {
  // Swipe
  addSwipeDistance: (v: number) => appendToArray(KEYS.swipeDistances, v),
  addSwipeDuration: (v: number) => appendToArray(KEYS.swipeDurations, v),
  addSwipeSpeed: (v: number) => appendToArray(KEYS.swipeSpeeds, v),
  addSwipeDirection: (v: number) => appendToArray(KEYS.swipeDirections, v),
  addSwipeAcceleration: (v: number) => appendToArray(KEYS.swipeAccelerations, v),
  // Typing
  addHoldTime: (v: number) => appendToArray(KEYS.holdTimes, v),
  addFlightTime: (v: number) => appendToArray(KEYS.flightTimes, v),
  addBackspaceRate: (v: number) => appendToArray(KEYS.backspaceRates, v),
  addTypingSpeed: (v: number) => appendToArray(KEYS.typingSpeeds, v),
  // For debugging or sending to backend
  getAll: async () => {
    const result: Record<string, number[]> = {};
    for (const key of Object.values(KEYS)) {
      const arr = await AsyncStorage.getItem(key);
      result[key] = arr ? JSON.parse(arr) : [];
    }
    return result;
  },
  clearAll: async () => {
    for (const key of Object.values(KEYS)) {
      await AsyncStorage.removeItem(key);
    }
  }
};