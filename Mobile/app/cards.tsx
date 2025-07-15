import React, { useState, useRef, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, TextInput, Alert, ScrollView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { Feather, MaterialCommunityIcons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { PanGestureHandler, GestureHandlerRootView, State as GestureState } from 'react-native-gesture-handler';
import { useSocket } from '../context/SocketContext';

// --- Typing Data Types ---
type TypingField = 'accountNumber' | 'cardType' | 'cardNo' | 'pin' | 'cvv' | 'expiry';

export default function CardsScreen() {
  const router = useRouter();
  const socket = useSocket();
  const [accountNumber, setAccountNumber] = useState('');
  const [cardType, setCardType] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [cardNo, setCardNo] = useState('');
  const [pin, setPin] = useState('');
  const [cvv, setCvv] = useState('');
  const [expiry, setExpiry] = useState('');
  const [cards, setCards] = useState<any[]>([]);
  const [user, setUser] = useState<any>(null);

  // --- Swipe Data States ---
  const [swipeDistancesNew, setSwipeDistancesNew] = useState<number[]>([]);
  const [swipeDurationsNew, setSwipeDurationsNew] = useState<number[]>([]);
  const [swipeSpeedsNew, setSwipeSpeedsNew] = useState<number[]>([]);
  const [swipeDirectionsNew, setSwipeDirectionsNew] = useState<number[]>([]);
  const [swipeAccelerationsNew, setSwipeAccelerationsNew] = useState<number[]>([]);
  const swipeStart = useRef<{ x: number; y: number; time: number } | null>(null);

  // --- Typing Data States ---
  const [holdTimesNew, setHoldTimesNew] = useState<number[]>([]);
  const [flightTimesNew, setFlightTimesNew] = useState<number[]>([]);
  const [backspaceRatesNew, setBackspaceRatesNew] = useState<number[]>([]);
  const [typingSpeedsNew, setTypingSpeedsNew] = useState<number[]>([]);

  const keyDownTimestamps = useRef<{ [key in TypingField]?: number }>({});
  const lastKeyUpTimestamp = useRef<number | null>(null);
  const lastTypedField = useRef<TypingField | null>(null);
  const backspaceCount = useRef<number>(0);
  const totalTyped = useRef<number>(0);
  const typingStartTime = useRef<number | null>(null);
  const [flagged, setFlagged] = useState<string[]>([]);
  

  useEffect(() => {
    (async () => {
      const stored = await AsyncStorage.getItem('cards');
      if (stored) setCards(JSON.parse(stored));
    })();
  }, []);

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

  useEffect(() => {
    socket.on('prediction-result', (msg: string) => {
      console.log('Received message:', msg);
      let data;
      try {
        data = JSON.parse(msg);
      } catch (e) {
        console.error('❌ Failed to parse prediction message:', e);
        return;
      }

      // Extract swipeRisk
      const swipeRisk = data?.swiping?.prediction_result?.risk_category;
      console.log('🧪 swipeRisk:', swipeRisk);

      if (!swipeRisk) return;

      // If critical risk → alert and logout
      if (swipeRisk === 'critical_risk') {
        Alert.alert(
          'Security Alert',
          'Critical risk detected. You will be logged out.',
          [
            {
              text: 'OK',
              onPress: () => {
                // Navigate to login or perform logout logic
                router.push('/login');
              },
            },
          ],
          { cancelable: false }
        );
        return;
      }

      // Otherwise, store risk in flagged
      setFlagged((prev) => {
        const updated = [...prev, swipeRisk];

        const mediumCount = updated.filter(
          (risk) => risk === 'medium_risk'
        ).length;
        const highCount = updated.filter(
          (risk) => risk === 'high_risk'
        ).length;

        console.log(
          `⚠️ Risks so far → Medium: ${mediumCount}, High: ${highCount}`
        );

        if (mediumCount >= 5 || highCount >= 2) {
          Alert.alert(
            'Security Alert',
            'Too many risky sessions detected. Logging out.',
          );
          router.push('/login');
        }

        return updated;
      });
    });
    return () => {
      socket.off('prediction-result');
    };
  }, [socket]);

  useEffect(() => {
    AsyncStorage.setItem('cards', JSON.stringify(cards));
  }, [cards]);

  const emitFeatureData = () => {
    if (!user || !user._id) return;
  
    const swipePresent = swipeDistancesNew.length > 0;
    const typingPresent = holdTimesNew.length > 0;
  
    if (!swipePresent && !typingPresent) return;
  
    const data: any = {
      user_id: user._id,
      data: {}
    };
  
    if (swipePresent) {
      Object.assign(data.data, {
        swipeDistancesNew,
        swipeDurationsNew,
        swipeSpeedsNew,
        swipeDirectionsNew,
        swipeAccelerationsNew
      });
    }
  
    if (typingPresent) {
      Object.assign(data.data, {
        holdTimesNew,
        flightTimesNew,
        backspaceRatesNew,
        typingSpeedsNew
      });
    }
  
    console.log("📤 Sending features:", data);
    if(holdTimesNew.length > 10 && flightTimesNew.length > 10 && backspaceRatesNew.length > 10 && typingSpeedsNew.length > 10) {
      socket.emit('send-features', data);
    }
  };
  

  const handleTyping = (text: string, prevText: string, setText: (v: string) => void, field: TypingField) => {
    const now = Date.now();
    if (typingStartTime.current === null) typingStartTime.current = now;
    totalTyped.current += Math.abs(text.length - prevText.length);

    if (keyDownTimestamps.current[field]) {
      const hold = now - keyDownTimestamps.current[field]!;
      setHoldTimesNew((prev) => [...prev, hold]);
    }
    keyDownTimestamps.current[field] = now;

    if (lastKeyUpTimestamp.current && lastTypedField.current !== null) {
      const flight = now - lastKeyUpTimestamp.current;
      setFlightTimesNew((prev) => [...prev, flight]);
    }
    lastTypedField.current = field;

    if (text.length < prevText.length) {
      backspaceCount.current += 1;
    }

    setText(text);

    setTimeout(() => {
      lastKeyUpTimestamp.current = Date.now();
      const elapsed = lastKeyUpTimestamp.current - (typingStartTime.current || lastKeyUpTimestamp.current);
      if (elapsed > 0) {
        const wpm = (totalTyped.current * 60) / (5 * (elapsed / 1000));
        setTypingSpeedsNew((prev) => [...prev, wpm]);
        setBackspaceRatesNew((prev) => [...prev, backspaceCount.current / (totalTyped.current || 1)]);
      }
    }, 0);

    emitFeatureData();
  };

  const onGestureEvent = React.useCallback(() => {}, []);

  const onHandlerStateChange = React.useCallback((event: any) => {
    const { state, absoluteX, absoluteY } = event.nativeEvent;
    if (state === GestureState.BEGAN) {
      swipeStart.current = { x: absoluteX, y: absoluteY, time: Date.now() };
    }
    if (state === GestureState.END && swipeStart.current) {
      const dx = absoluteX - swipeStart.current.x;
      const dy = absoluteY - swipeStart.current.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      const duration = Date.now() - swipeStart.current.time;
      const speed = duration > 0 ? distance / duration : 0;

      let angle = Math.atan2(dy, dx) * (180 / Math.PI);
      if (angle < 0) angle += 360;

      const acceleration = duration > 0 ? (1e5) * speed / duration : 0;

      setSwipeDistancesNew((prev) => [...prev, distance]);
      setSwipeDurationsNew((prev) => [...prev, duration]);
      setSwipeSpeedsNew((prev) => [...prev, speed]);
      setSwipeDirectionsNew((prev) => [...prev, angle]);
      setSwipeAccelerationsNew((prev) => [...prev, acceleration]);

      setTimeout(emitFeatureData, 0);
      swipeStart.current = null;
      emitFeatureData();
    }
  }, [swipeDistancesNew, swipeDurationsNew, swipeSpeedsNew, swipeDirectionsNew, swipeAccelerationsNew]);

  const handleSubmit = async () => {
    if (!accountNumber || !cardType || !cardNo) {
      Alert.alert('Error', 'Please fill all required fields.');
      return;
    }
    setCards([...cards, { accountNumber, cardType, cardNo, expiry }]);
    Alert.alert('Success', 'Card has been added successfully!');
    setAccountNumber('');
    setCardType('');
    setCardNo('');
    setPin('');
    setCvv('');
    setExpiry('');
  };

  const handleRemoveCard = (idxToRemove: number) => {
    const updatedCards = cards.filter((_, idx) => idx !== idxToRemove);
    setCards(updatedCards);
  };

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <PanGestureHandler
        onGestureEvent={onGestureEvent}
        onHandlerStateChange={onHandlerStateChange}
      >
        <View style={{ flex: 1 }}>
          <ScrollView contentContainerStyle={{ flexGrow: 1, alignItems: 'center', backgroundColor: '#f7fafd', paddingTop: 80 }}>
            <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
              <Feather name="arrow-left" size={24} color="#244A85" />
              <Text style={styles.backText}>Back</Text>
            </TouchableOpacity>

            {/* Card List */}
            <View style={{ width: '85%', marginBottom: 24 }}>
              {cards.length === 0 ? (
                <TouchableOpacity style={styles.addBankBox}>
                  <MaterialCommunityIcons name="bank" size={32} color="#2CC7A6" />
                  <Text style={styles.addBankText}>Add card</Text>
                </TouchableOpacity>
              ) : (
                cards.map((card, idx) => (
                  <View key={idx} style={styles.cardBox}>
                    <MaterialCommunityIcons name="credit-card-outline" size={40} color="#2CC7A6" />
                    <View style={{ marginLeft: 12, flex: 1 }}>
                      <Text style={{ fontWeight: 'bold', fontSize: 16, color: '#244A85' }}>
                        {card.cardType === 'Credit' ? 'Credit Card' : 'Debit Card'} {card.cardNo.slice(-4)}
                      </Text>
                      <Text style={{ color: '#888', fontSize: 14 }}>
                        {card.accountNumber ? `A/C: ****${card.accountNumber.slice(-4)}` : ''}
                      </Text>
                      <Text style={{ color: '#888', fontSize: 13 }}>
                        Expiry: {card.expiry}
                      </Text>
                    </View>
                    <TouchableOpacity onPress={() => handleRemoveCard(idx)} style={styles.removeBtn}>
                      <Feather name="trash-2" size={22} color="#E53935" />
                    </TouchableOpacity>
                  </View>
                ))
              )}
            </View>
            <Text style={styles.heading}>Add Card</Text>
            <View style={styles.inputBox}>
              <Text style={styles.label}>Account Number</Text>
              <TextInput
                style={styles.input}
                placeholder="Enter account number"
                keyboardType="number-pad"
                maxLength={18}
                value={accountNumber}
                onChangeText={text => handleTyping(text, accountNumber, setAccountNumber, 'accountNumber')}
              />
            </View>
            <View style={styles.inputBox}>
              <Text style={styles.label}>Card Type</Text>
              <TouchableOpacity
                style={[styles.input, { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }]}
                onPress={() => setShowDropdown(!showDropdown)}
                activeOpacity={0.8}
              >
                <Text style={{ color: cardType ? '#244A85' : '#888' }}>
                  {cardType || 'Select Card Type'}
                </Text>
                <Feather name={showDropdown ? 'chevron-up' : 'chevron-down'} size={20} color="#244A85" />
              </TouchableOpacity>
              {showDropdown && (
                <View style={styles.dropdown}>
                  <TouchableOpacity onPress={() => { setCardType('Debit'); setShowDropdown(false); }}>
                    <Text style={styles.dropdownItem}>Debit</Text>
                  </TouchableOpacity>
                  <TouchableOpacity onPress={() => { setCardType('Credit'); setShowDropdown(false); }}>
                    <Text style={styles.dropdownItem}>Credit</Text>
                  </TouchableOpacity>
                </View>
              )}
            </View>
            <View style={styles.inputBox}>
              <Text style={styles.label}>Card No</Text>
              <TextInput
                style={styles.input}
                placeholder="Enter card number"
                keyboardType="number-pad"
                maxLength={16}
                value={cardNo}
                onChangeText={text => handleTyping(text, cardNo, setCardNo, 'cardNo')}
              />
            </View>
            <View style={styles.inputBox}>
              <Text style={styles.label}>Pin</Text>
              <TextInput
                style={styles.input}
                placeholder="Enter pin"
                secureTextEntry
                keyboardType="number-pad"
                maxLength={6}
                value={pin}
                onChangeText={text => handleTyping(text, pin, setPin, 'pin')}
              />
            </View>
            <View style={styles.inputBox}>
              <Text style={styles.label}>CVV</Text>
              <TextInput
                style={styles.input}
                placeholder="Enter CVV"
                secureTextEntry
                keyboardType="number-pad"
                maxLength={4}
                value={cvv}
                onChangeText={text => handleTyping(text, cvv, setCvv, 'cvv')}
              />
            </View>
            <View style={styles.inputBox}>
              <Text style={styles.label}>Expiry Date</Text>
              <TextInput
                style={styles.input}
                placeholder="MM/YY"
                keyboardType="numbers-and-punctuation"
                maxLength={5}
                value={expiry}
                onChangeText={text => handleTyping(text, expiry, setExpiry, 'expiry')}
              />
            </View>
            <TouchableOpacity style={styles.submitBtn} onPress={handleSubmit}>
              <Text style={styles.submitBtnText}>Submit</Text>
            </TouchableOpacity>
          </ScrollView>
        </View>
      </PanGestureHandler>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f7fafd' },
  backBtn: { flexDirection: 'row', alignItems: 'center', position: 'absolute', top: 40, left: 16 },
  backText: { marginLeft: 4, fontSize: 16, color: '#244A85' },
  text: { fontSize: 24, fontWeight: 'bold', color: '#244A85', marginBottom: 8 },
  subtext: { fontSize: 16, color: '#244A85', opacity: 0.7 },
  heading: { fontSize: 22, fontWeight: 'bold', color: '#244A85', marginTop: 32, marginBottom: 16 },
  inputBox: { width: '80%', marginBottom: 14 },
  label: { fontSize: 15, color: '#244A85', marginBottom: 4, marginLeft: 2 },
  input: { backgroundColor: '#fff', borderRadius: 8, padding: 12, fontSize: 16, borderWidth: 1, borderColor: '#e0e0e0' },
  dropdown: {
    backgroundColor: '#fff',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    marginTop: 2,
    width: '100%',
    position: 'absolute',
    zIndex: 10,
  },
  dropdownItem: {
    padding: 12,
    fontSize: 16,
    color: '#244A85',
  },
  submitBtn: {
    backgroundColor: '#244A85',
    borderRadius: 8,
    paddingVertical: 14,
    paddingHorizontal: 40,
    marginTop: 18,
    alignItems: 'center',
  },
  submitBtnText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  cardBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  addBankBox: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderStyle: 'dashed',
    borderColor: '#2CC7A6',
    borderRadius: 10,
    padding: 16,
    justifyContent: 'center',
    marginBottom: 8,
  },
  addBankText: {
    color: '#244A85',
    fontSize: 16,
    marginLeft: 10,
  },
  removeBtn: {
    marginLeft: 10,
    padding: 6,
    borderRadius: 6,
    backgroundColor: '#fdecea',
    alignItems: 'center',
    justifyContent: 'center',
  },
});