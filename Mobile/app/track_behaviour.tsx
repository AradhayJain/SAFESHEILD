import React, { useState, useRef, useEffect } from 'react';
import { View, Text, StyleSheet, TextInput, ScrollView, KeyboardAvoidingView, Platform, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { GestureHandlerRootView, PanGestureHandler, PanGestureHandlerGestureEvent } from 'react-native-gesture-handler';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const questions = [
  "Describe yourself in one paragraph.",
  "Describe your experience with online banking. What features do you use the most?",
  "Explain why you chose your current bank account type and how it benefits you.",
  "How do you keep track of your transactions and account balances?"
];

export default function TrackBehaviourScreen() {
  const router = useRouter();
  const [current, setCurrent] = useState(0);
  const [answers, setAnswers] = useState(Array(questions.length).fill(''));
  const [swipeCount, setSwipeCount] = useState(Array(questions.length).fill(0));
  const [user, setUser] = useState<any>(null);

  const [swipeDistances, setSwipeDistances] = useState<number[]>([]);
  const [swipeDurations, setSwipeDurations] = useState<number[]>([]);
  const [swipeSpeeds, setSwipeSpeeds] = useState<number[]>([]);
  const [swipeDirections, setSwipeDirections] = useState<number[]>([]);
  const [swipeAccelerations, setSwipeAccelerations] = useState<number[]>([]);

  const [typingData, setTypingData] = useState(
    Array(questions.length).fill(null).map(() => ({
      keyCount: 0,
      backspaceCount: 0,
      startTime: null as null | number,
      endTime: null as null | number,
      holdTimes: [] as number[],
      flightTimes: [] as number[],
      typingSpeed: 0,
      typingSpeedHistory: [] as number[],
      wpm: 0,
      backspaceRate: 0,
      backspaceRateHistory: [] as number[],
      wordCount: 0,
    }))
  );

  const keyDownTime = useRef<number | null>(null);
  const lastKeyUpTime = useRef<number | null>(null);
  const firstKeyDownTime = useRef<number | null>(null);
  const gestureStart = useRef<{ x: number, y: number, t: number } | null>(null);
  const scrollRef = useRef<ScrollView>(null);

  useEffect(() => {
    const loadStoredData = async () => {
      try {
        const storedUser = await AsyncStorage.getItem('authUser');
        if (storedUser) setUser(JSON.parse(storedUser));
      } catch (error) {
        console.error('Error loading from AsyncStorage', error);
      }
    };
    loadStoredData();
  }, []);

  const handleTyping = (text: string) => {
    const now = Date.now();
    if (firstKeyDownTime.current === null) {
      firstKeyDownTime.current = now;
    }

    if (keyDownTime.current !== null && lastKeyUpTime.current !== null) {
      setTypingData(prev => {
        const updated = [...prev];
        updated[current].flightTimes.push(now - lastKeyUpTime.current!);
        return updated;
      });
    }

    keyDownTime.current = now;

    if (answers[current].length > text.length) {
      setTypingData(prev => {
        const updated = [...prev];
        updated[current].backspaceCount++;
        return updated;
      });
    } else {
      setTypingData(prev => {
        const updated = [...prev];
        updated[current].keyCount++;
        return updated;
      });
    }

    setAnswers(prev => {
      const updated = [...prev];
      updated[current] = text;
      return updated;
    });

    setTimeout(() => {
      const holdTime = Date.now() - keyDownTime.current!;
      lastKeyUpTime.current = Date.now();

      setTypingData(prev => {
        const updated = [...prev];
        updated[current].holdTimes.push(holdTime);
        updated[current].endTime = lastKeyUpTime.current!;

        const durationSeconds =
          (updated[current].endTime! - (updated[current].startTime || firstKeyDownTime.current!)) / 1000;

        const charPerSec = durationSeconds > 0
          ? (updated[current].keyCount / durationSeconds)
          : 0;

        const wpm = durationSeconds > 0
          ? (updated[current].keyCount / 5) / (durationSeconds / 60)
          : 0;

        const backspaceRate = updated[current].keyCount > 0
          ? updated[current].backspaceCount / updated[current].keyCount
          : 0;

        const wordCount = answers[current].trim().length > 0
          ? answers[current].trim().split(/\s+/).length
          : 0;

        updated[current] = {
          ...updated[current],
          startTime: updated[current].startTime || firstKeyDownTime.current!,
          typingSpeed: charPerSec,
          typingSpeedHistory: [...updated[current].typingSpeedHistory, charPerSec],
          wpm,
          backspaceRate,
          backspaceRateHistory: [...updated[current].backspaceRateHistory, backspaceRate],
          wordCount,
        };

        return updated;
      });
    }, 100);
  };

  const onGestureEvent = (event: PanGestureHandlerGestureEvent) => {};

  const onHandlerStateChange = (event: PanGestureHandlerGestureEvent) => {
    const { nativeEvent } = event;
    if (nativeEvent.state === 2) {
      gestureStart.current = { x: nativeEvent.x, y: nativeEvent.y, t: Date.now() };
    }
    if (nativeEvent.state === 5 && gestureStart.current) {
      const { x, y, t } = gestureStart.current;
      const dx = nativeEvent.x - x;
      const dy = nativeEvent.y - y;
      const duration = Date.now() - t;
      const distance = Math.sqrt(dx * dx + dy * dy);
      const speed = duration > 0 ? distance / duration : 0;
      let direction = Math.atan2(dy, dx) * (180 / Math.PI);
      if (direction < 0) direction += 360;
      const acceleration = duration > 0 ? (1e5) * speed / duration : 0;

      if (Math.abs(dx) > 50) {
        if (!answers[current] || answers[current].trim() === '') {
          Alert.alert('Please answer the question before proceeding.');
          gestureStart.current = null;
          return;
        }

        setSwipeCount(prev => {
          const updated = [...prev];
          updated[current] = updated[current] + 1;
          return updated;
        });

        setSwipeDistances(prev => [...prev, distance]);
        setSwipeDurations(prev => [...prev, duration]);
        setSwipeSpeeds(prev => [...prev, speed]);
        setSwipeDirections(prev => [...prev, direction]);
        setSwipeAccelerations(prev => [...prev, acceleration]);

        if (swipeCount[current] + 1 >= 4) {
          keyDownTime.current = null;
          lastKeyUpTime.current = null;
          firstKeyDownTime.current = null;

          setTypingData(prev => {
            const updated = [...prev];
            if (current + 1 < questions.length) {
              updated[current + 1] = {
                keyCount: 0,
                backspaceCount: 0,
                startTime: null,
                endTime: null,
                holdTimes: [],
                flightTimes: [],
                typingSpeed: 0,
                typingSpeedHistory: [],
                wpm: 0,
                backspaceRate: 0,
                backspaceRateHistory: [],
                wordCount: 0,
              };
            }
            return updated;
          });

          if (current < questions.length - 1) {
            setCurrent(current + 1);
          } else {
            const holdTimes = typingData.flatMap(q => q.holdTimes);
            const flightTimes = typingData.flatMap(q => q.flightTimes);
            const backspaceRates = typingData.map(q => q.backspaceRate);
            const typingSpeeds = typingData.map(q => q.wpm);
            const backspaceRateHistory = typingData.flatMap(q => q.backspaceRateHistory);
            const typingSpeedHistory = typingData.flatMap(q => q.typingSpeedHistory);

            setTimeout(() => {
              console.log('FINAL holdTimes:', holdTimes);
              console.log('FINAL flightTimes:', flightTimes);
              console.log('FINAL backspaceRateHistory:', backspaceRateHistory);
              console.log('FINAL backspaceRate:', backspaceRates);
              console.log('FINAL typingSpeedHistory:', typingSpeedHistory);
              console.log('FINAL typingSpeed:', typingSpeeds);
              console.log('FINAL swipeDistances', swipeDistances);
              console.log('FINAL swipeDurations:', swipeDurations); 
              console.log('FINAL swipeSpeeds:', swipeSpeeds); 
              console.log('FINAL swipeDirections:', swipeDirections); 
            }, 10);
          }
        }
      }

      gestureStart.current = null;
    }
  };

  const handleSubmit = async () => {
    try {
      const holdTimes = typingData.flatMap(q => q.holdTimes);
      const flightTimes = typingData.flatMap(q => q.flightTimes);
      const backspaceRates = typingData.map(q => q.backspaceRate);
      const typingSpeeds = typingData.map(q => q.wpm);
      const backspaceRateHistory = typingData.flatMap(q => q.backspaceRateHistory);
      const typingSpeedHistory = typingData.flatMap(q => q.typingSpeedHistory);

      const { data } = await axios.post('http://192.168.1.6:9001/api/data/getData', {
        userId: user._id,
        data2: {
          swipeDistances,
          swipeDurations,
          swipeSpeeds,
          swipeDirections,
          swipeAccelerations,
          holdTimes,
          flightTimes,
          backspaceRates : backspaceRateHistory,
          typingSpeeds : typingSpeedHistory,
        },
      });

      if (data) console.log('Data received:', data);
      Alert.alert('Data submitted successfully!');
      router.replace('/login');
    } catch (error) {
      Alert.alert('Submission failed', (error as any)?.response?.data?.message || 'Unknown error');
    }
  };

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 60 : 0}
      >
        <PanGestureHandler
          onGestureEvent={onGestureEvent}
          onHandlerStateChange={onHandlerStateChange}
        >
          <ScrollView
            ref={scrollRef}
            contentContainerStyle={styles.scrollContainer}
            keyboardShouldPersistTaps="handled"
          >
            <View style={styles.container}>
              <Text style={styles.heading}>Behaviour Tracking Data Collection</Text>
              <Text style={styles.subheading}>
                To enable the behaviour tracking system, please provide a detailed response (at least one full line) to each of the following questions.
                {"\n\n"}
                <Text style={{ color: '#b0b0b0', fontSize: 13 }}>
                  Privacy Notice: Your written responses are not stored. Only your typing and swiping patterns are measured for behavioural analysis.
                </Text>
              </Text>
              <View style={styles.questionBox}>
                <Text style={styles.question}>{questions[current]}</Text>
                <TextInput
                  style={styles.input}
                  placeholder="Type your answer..."
                  value={answers[current]}
                  onChangeText={handleTyping}
                  multiline
                  onFocus={() => {
                    setTimeout(() => {
                      scrollRef.current?.scrollToEnd({ animated: true });
                    }, 300);
                  }}
                />
                <Text style={styles.swipeHint}>
                  Swipe 4 times to go to next question ({swipeCount[current]}/4)
                </Text>
                {current === questions.length - 1 && swipeCount[current] >= 3 && (
                  <View style={{ marginTop: 16, width: '100%' }}>
                    <Text
                      style={{
                        backgroundColor: '#244A85',
                        color: '#fff',
                        textAlign: 'center',
                        padding: 12,
                        borderRadius: 8,
                        fontWeight: 'bold',
                        fontSize: 16,
                      }}
                      onPress={handleSubmit}
                    >
                      Submit
                    </Text>
                  </View>
                )}
              </View>
              <Text style={styles.progress}>Step {current + 1} of {questions.length}</Text>
            </View>
          </ScrollView>
        </PanGestureHandler>
      </KeyboardAvoidingView>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  scrollContainer: { flexGrow: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f7fafd' },
  container: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 20 },
  heading: { fontSize: 22, fontWeight: 'bold', color: '#244A85', marginBottom: 10, textAlign: 'center' },
  subheading: { fontSize: 14, color: '#244A85', marginBottom: 24, textAlign: 'center' },
  questionBox: { width: '100%', backgroundColor: '#fff', borderRadius: 12, padding: 20, alignItems: 'center', elevation: 2 },
  question: { fontSize: 17, color: '#244A85', marginBottom: 12, textAlign: 'center', fontWeight: '500' },
  input: { width: '100%', minHeight: 40, backgroundColor: '#f2f2f2', borderRadius: 8, padding: 10, fontSize: 16, marginBottom: 10 },
  swipeHint: { fontSize: 13, color: '#888', marginTop: 6, textAlign: 'center' },
  progress: { marginTop: 18, fontSize: 13, color: '#244A85', fontWeight: 'bold' },
});