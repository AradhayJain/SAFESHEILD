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

  // --- Gesture/Swipe Data Arrays ---
  // Store all data in 1D arrays (not per question)
  const [swipeDistances, setSwipeDistances] = useState<number[]>([]);
  const [swipeDurations, setSwipeDurations] = useState<number[]>([]);
  const [swipeSpeeds, setSwipeSpeeds] = useState<number[]>([]);
  const [swipeDirections, setSwipeDirections] = useState<number[]>([]);
  const [swipeAccelerations, setSwipeAccelerations] = useState<number[]>([]);

  // --- Typing Data Arrays ---
  const [holdTimes, setHoldTimes] = useState<number[]>([]);
  const [flightTimes, setFlightTimes] = useState<number[][]>(Array(questions.length).fill([]));
  const [backspaceRates, setBackspaceRates] = useState<number[]>([]);
  const [typingSpeeds, setTypingSpeeds] = useState<number[]>([]);

  // Typing state for tracking
  const keyDownTime = useRef<number | null>(null);
  const lastKeyUpTime = useRef<number | null>(null);
  const firstKeyDownTime = useRef<number | null>(null);
  const totalKeys = useRef<number[]>(Array(questions.length).fill(0));
  const backspaceCount = useRef<number[]>(Array(questions.length).fill(0));

  const gestureStart = useRef<{x: number, y: number, t: number} | null>(null);
  const scrollRef = useRef<ScrollView>(null);

  // Typing tracking (simulate keyDown/keyUp for mobile)
  useEffect(() => {
    const loadStoredData = async () => {
      try {
        // const storedToken = await AsyncStorage.getItem('authToken');
        const storedUser = await AsyncStorage.getItem('authUser');
        // if (storedToken) setToken(storedToken);
        if (storedUser) setUser(JSON.parse(storedUser));
      } catch (error) {
        console.error('Error loading from AsyncStorage', error);
      }
    };

    loadStoredData();
  }, []);

  const handleTyping = (text: string) => {
    // Simulate keyDown
    const now = Date.now();
    if (firstKeyDownTime.current === null) firstKeyDownTime.current = now;
    if (keyDownTime.current !== null && lastKeyUpTime.current !== null) {
      // Flight time: time between last key up and this key down
      setFlightTimes(prev => {
        const updated = [...prev];
        updated[current] = [...(updated[current] || []), now - lastKeyUpTime.current!];
        return updated;
      });
    }
    keyDownTime.current = now;

    // Detect backspace
    if (answers[current].length > text.length) {
      backspaceCount.current[current] = backspaceCount.current[current] + 1;
    } else {
      totalKeys.current[current] = totalKeys.current[current] + 1;
    }

    setAnswers(prev => {
      const updated = [...prev];
      updated[current] = text;
      return updated;
    });

    // Simulate keyUp (immediately after keyDown for mobile)
    const upNow = Date.now();
    if (keyDownTime.current !== null) {
      setTimeout(() => {
        setHoldTimes(prev => [...prev, Date.now() - keyDownTime.current!]);
        lastKeyUpTime.current = Date.now();
      }, 100); // delay in ms, e.g. 100ms
    }

    // Typing speed: total keys / (lastKeyUp - firstKeyDown) in chars/sec
    if (firstKeyDownTime.current && lastKeyUpTime.current && totalKeys.current[current] > 0) {
      setTypingSpeeds(prev => {
        const updated = [...prev];
        updated[current] = totalKeys.current[current] / ((lastKeyUpTime.current! - firstKeyDownTime.current!) / 1000);
        return updated;
      });
    }

    // Backspace rate: # of ⌫ presses / total keys
      if (totalKeys.current[current] > 0) {
      // Calculate backspace rate
          const rate = backspaceCount.current[current] / totalKeys.current[current];
          setBackspaceRates(prev => {
          const updated = [...prev];
          updated[current] = rate;
          return updated;
      });

      setTypingSpeeds(prev => {
        const updated = [...prev];
        const elapsedMs = lastKeyUpTime.current! - firstKeyDownTime.current!;
        const elapsedMinutes = elapsedMs / (1000 * 60);
        const wpm = (totalKeys.current[current] / 5) / elapsedMinutes;
        updated[current] = wpm;
        return updated;
      });

    }
  };

  const onGestureEvent = (event: PanGestureHandlerGestureEvent) => {
    // No-op
  };

  const onHandlerStateChange = (event: PanGestureHandlerGestureEvent) => {
    const { nativeEvent } = event;
    if (nativeEvent.state === 2) { // BEGAN
      gestureStart.current = { x: nativeEvent.x, y: nativeEvent.y, t: Date.now() };
    }
    if (nativeEvent.state === 5 && gestureStart.current) { // END
      const x1 = gestureStart.current.x;
      const y1 = gestureStart.current.y;
      const t1 = gestureStart.current.t;
      const x2 = nativeEvent.x;
      const y2 = nativeEvent.y;
      const t2 = Date.now();

      const dx = x2 - x1;
      const dy = y2 - y1;
      const distance = Math.sqrt(dx * dx + dy * dy);
      const duration = t2 - t1;
      const speed = duration > 0 ? distance / duration : 0;
      let direction = Math.atan2(dy, dx);
      if(direction < 0) direction += 360;
      const acceleration = duration > 0 ? (1e5)*speed / duration : 0;

      if (Math.abs(dx) > 50) {
        // Prevent swipe if answer is empty
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

        // After 3 swipes, move to next question or finish
        if (swipeCount[current] + 1 >= 3) {
          // Reset typing trackers for next question
          keyDownTime.current = null;
          lastKeyUpTime.current = null;
          firstKeyDownTime.current = null;
          totalKeys.current[current + 1] = 0;
          backspaceCount.current[current + 1] = 0;

          if (current < questions.length - 1) {
            setCurrent(current + 1);
          } else {
            // Remove router.replace('/login') here
            setTimeout(() => {
              console.log('FINAL swipeDistances:', swipeDistances);
              console.log('FINAL swipeDurations:', swipeDurations);
              console.log('FINAL swipeSpeeds:', swipeSpeeds);
              console.log('FINAL swipeDirections:', swipeDirections);
              console.log('FINAL swipeAccelerations:', swipeAccelerations);
              console.log('FINAL holdTimes:', holdTimes);
              console.log('FINAL flightTimes:', flightTimes);
              console.log('FINAL backspaceRates:', backspaceRates);
              console.log('FINAL typingSpeeds:', typingSpeeds);
              // Do NOT navigate away here
            }, 0);
          }
        }
      }
      gestureStart.current = null;
    }
  };

  // Submit handler
  const handleSubmit = async () => {
    try {
      const { data } = await axios.post('http://192.168.1.6:9001/api/data/getData', {userId:user._id,data2:{
        swipeDistances,
        swipeDurations,
        swipeSpeeds,
        swipeDirections,
        swipeAccelerations,
        holdTimes,
        flightTimes,
        backspaceRates,
        typingSpeeds,
      }});
      if(data){console.log('Data received:', data);}
      Alert.alert('Data submitted successfully!');
      router.replace('/login');
    } catch (error) {
      Alert.alert('Submission failed', (error as any)?.response?.data?.message || (typeof error === 'string' ? error : 'Unknown error'));
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
                  Swipe 3 times to go to next question ({swipeCount[current]}/3)
                </Text>
                {/* Show Submit button only on last question and after 3 swipes */}
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
                        overflow: 'hidden',
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
