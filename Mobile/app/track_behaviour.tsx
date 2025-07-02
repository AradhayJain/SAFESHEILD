import React, { useState, useRef } from 'react';
import { View, Text, StyleSheet, TextInput, ScrollView, KeyboardAvoidingView, Platform, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { GestureHandlerRootView, PanGestureHandler, PanGestureHandlerGestureEvent } from 'react-native-gesture-handler';

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
  const [typingTimes, setTypingTimes] = useState<number[][]>(Array(questions.length).fill([]).map(() => []));
  const [lastTypeTime, setLastTypeTime] = useState<number | null>(null);

  // Store all raw swipes for each question
  const [swipeSpeeds, setSwipeSpeeds] = useState<number[][]>(Array(questions.length).fill([]).map(() => []));
  const [swipeAngles, setSwipeAngles] = useState<number[][]>(Array(questions.length).fill([]).map(() => []));
  // Store mean/std for each question after 3 swipes
  const [swipeStats, setSwipeStats] = useState<{speedMean: number, speedStd: number, angleMean: number, angleStd: number}[]>(
    Array(questions.length).fill({speedMean: 0, speedStd: 0, angleMean: 0, angleStd: 0})
  );

  const gestureStart = useRef<{x: number, y: number, t: number} | null>(null);
  const scrollRef = useRef<ScrollView>(null);

  // Typing speed tracking per question
  const handleTyping = (text: string) => {
    const now = Date.now();
    if (lastTypeTime !== null) {
      setTypingTimes(prev => {
        const updated = [...prev];
        updated[current] = [...updated[current], now - lastTypeTime];
        return updated;
      });
    }
    setLastTypeTime(now);
    setAnswers(prev => {
      const updated = [...prev];
      updated[current] = text;
      return updated;
    });
  };

  // Utility functions
  const mean = (arr: number[]) => arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
  const std = (arr: number[]) => {
    const m = mean(arr);
    return arr.length ? Math.sqrt(arr.reduce((a, b) => a + (b - m) ** 2, 0) / arr.length) : 0;
  };

  // PanGestureHandler event
  const onGestureEvent = (event: PanGestureHandlerGestureEvent) => {
    // No-op
  };

  const onHandlerStateChange = (event: PanGestureHandlerGestureEvent) => {
    const { nativeEvent } = event;
    if (nativeEvent.state === 2) { // BEGAN
      gestureStart.current = { x: nativeEvent.x, y: nativeEvent.y, t: Date.now() };
    }
    if (nativeEvent.state === 5 && gestureStart.current) { // END
      const dx = nativeEvent.x - gestureStart.current.x;
      const dy = nativeEvent.y - gestureStart.current.y;
      const dt = Date.now() - gestureStart.current.t;
      const distance = Math.sqrt(dx * dx + dy * dy);
      if (dt > 0 && Math.abs(dx) > 50) {
        // Prevent swipe if answer is empty
        if (!answers[current] || answers[current].trim() === '') {
          Alert.alert('Please answer the question before proceeding.');
          gestureStart.current = null;
          return;
        }
        const speed = distance / dt;
        const angle = Math.atan2(dy, dx) * (180 / Math.PI);

        setSwipeSpeeds(prev => {
          const updated = [...prev];
          updated[current] = [...updated[current], speed];
          return updated;
        });
        setSwipeAngles(prev => {
          const updated = [...prev];
          updated[current] = [...updated[current], angle];
          return updated;
        });

        // After updating, check if 3 swipes are done for this question
        setTimeout(() => {
          // Use latest values
          setSwipeSpeeds(prevSpeeds => {
            setSwipeAngles(prevAngles => {
              const speeds = prevSpeeds[current] || [];
              const angles = prevAngles[current] || [];
              if (speeds.length >= 3 && angles.length >= 3 && (!swipeStats[current] || swipeStats[current].speedMean === 0)) {
                const stats = {
                  speedMean: mean(speeds.slice(0, 3)),
                  speedStd: std(speeds.slice(0, 3)),
                  angleMean: mean(angles.slice(0, 3)),
                  angleStd: std(angles.slice(0, 3)),
                };
                setSwipeStats(prevStats => {
                  const updated = [...prevStats];
                  updated[current] = stats;
                  return updated;
                });
                // Move to next question after 3 swipes
                if (current < questions.length - 1) {
                  setCurrent(current + 1);
                  setLastTypeTime(null);
                } else {
                  router.replace('/login');
                }
              }
              return prevAngles;
            });
            return prevSpeeds;
          });
        }, 0);
      }
      gestureStart.current = null;
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
                <Text style={styles.swipeHint}>Swipe 3 times to go to next question</Text>
                <View style={{ marginTop: 10 }}>
                  <Text style={styles.stats}>
                    Typing speed (ms): mean={mean(typingTimes[current]).toFixed(2)}, std={std(typingTimes[current]).toFixed(2)}
                  </Text>
                  <Text style={styles.stats}>
                    Swipe speed (px/ms): {swipeStats[current]?.speedMean?.toFixed(4) ?? '0.0000'} (mean), {swipeStats[current]?.speedStd?.toFixed(4) ?? '0.0000'} (std)
                  </Text>
                  <Text style={styles.stats}>
                    Swipe angle (deg): {swipeStats[current]?.angleMean?.toFixed(2) ?? '0.00'} (mean), {swipeStats[current]?.angleStd?.toFixed(2) ?? '0.00'} (std)
                  </Text>
                  {/* Debug: show raw values */}
                  <Text style={styles.stats}>
                    Typing times: [{typingTimes[current].join(', ')}]
                  </Text>
                  <Text style={styles.stats}>
                    Swipe speeds: [{swipeSpeeds[current].join(', ')}]
                  </Text>
                  <Text style={styles.stats}>
                    Swipe angles: [{swipeAngles[current].join(', ')}]
                  </Text>
                </View>
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
  stats: { fontSize: 12, color: '#888', marginBottom: 2 },
  progress: { marginTop: 18, fontSize: 13, color: '#244A85', fontWeight: 'bold' },
});