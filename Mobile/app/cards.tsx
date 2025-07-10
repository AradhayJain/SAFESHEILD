import React, { useState, useRef, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, TextInput, Alert, ScrollView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { Feather, MaterialCommunityIcons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { PanGestureHandler, GestureHandlerRootView, State as GestureState } from 'react-native-gesture-handler';
import { useSocket } from './SocketContext';

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
  const [swipeDistances, setSwipeDistances] = useState<number[]>([]);
  const [swipeDurations, setSwipeDurations] = useState<number[]>([]);
  const [swipeSpeeds, setSwipeSpeeds] = useState<number[]>([]);
  const [swipeDirections, setSwipeDirections] = useState<string[]>([]);
  const [swipeAccelerations, setSwipeAccelerations] = useState<number[]>([]);
  const swipeStart = useRef<{ x: number; y: number; time: number } | null>(null);
  const lastVelocity = useRef<number>(0);

  // --- Typing Data States ---
  const [holdTimes, setHoldTimes] = useState<number[]>([]);
  const [flightTimes, setFlightTimes] = useState<number[]>([]);
  const [backspaceRates, setBackspaceRates] = useState<number[]>([]);
  const [typingSpeeds, setTypingSpeeds] = useState<number[]>([]);

  // For tracking typing
  const keyDownTimestamps = useRef<{ [key in TypingField]?: number }>({});
  const lastKeyUpTimestamp = useRef<number | null>(null);
  const lastTypedField = useRef<TypingField | null>(null);
  const backspaceCount = useRef<number>(0);
  const totalTyped = useRef<number>(0);
  const typingStartTime = useRef<number | null>(null);

  // Load cards from AsyncStorage on mount
  useEffect(() => {
    (async () => {
      const stored = await AsyncStorage.getItem('cards');
      if (stored) setCards(JSON.parse(stored));
    })();
  }, []);

  useEffect(() => {
    const loadStoredData = async () => {
      try {
        const storedToken = await AsyncStorage.getItem('authToken');
        const storedUser = await AsyncStorage.getItem('authUser');
        if (storedUser) setUser(JSON.parse(storedUser));
      } catch (error) {
        console.error('Error loading from AsyncStorage', error);
      }
    };

    loadStoredData();
  }, []);

  useEffect(() => {
    // Receive messages from server
    socket.on('prediction-result', (msg: string) => {
      console.log('Received message:', msg);
    });

    return () => {
      socket.off('prediction-result');
    };
  }, [socket]);

  // Save cards to AsyncStorage whenever cards change
  useEffect(() => {
    AsyncStorage.setItem('cards', JSON.stringify(cards));
  }, [cards]);

  // --- Typing Handler ---
  const handleTyping = (text: string, prevText: string, setText: (v: string) => void, field: TypingField) => {
    const now = Date.now();

    // Typing speed
    if (typingStartTime.current === null) typingStartTime.current = now;
    totalTyped.current += Math.abs(text.length - prevText.length);

    // Hold time (simulate as time between prev and now for each change)
    if (keyDownTimestamps.current[field]) {
      const hold = now - keyDownTimestamps.current[field]!;
      setHoldTimes((prev) => [...prev, hold]);
    }
    keyDownTimestamps.current[field] = now;

    // Flight time (time between last key up and this key down)
    if (lastKeyUpTimestamp.current && lastTypedField.current !== null) {
      const flight = now - lastKeyUpTimestamp.current;
      setFlightTimes((prev) => [...prev, flight]);
    }
    lastTypedField.current = field;

    // Backspace rate
    if (text.length < prevText.length) {
      backspaceCount.current += 1;
    }

    setText(text);

    // After a short delay, treat as key up
    setTimeout(() => {
      lastKeyUpTimestamp.current = Date.now();
      // After each key up, update typing speed and backspace rate
      const elapsed = lastKeyUpTimestamp.current - (typingStartTime.current || lastKeyUpTimestamp.current);
      if (elapsed > 0) {
        setTypingSpeeds((prev) => [...prev, totalTyped.current / (elapsed / 1000)]); // chars/sec
        setBackspaceRates((prev) => [...prev, backspaceCount.current / (totalTyped.current || 1)]);
      }
    }, 0);

    // Print all data to terminal after each change
    printAllData();
  };

  // --- Swipe Handler ---
  const onGestureEvent = React.useCallback((event: any) => {
    // No-op, required for PanGestureHandler
  }, []);

  const onHandlerStateChange = React.useCallback((event: any) => {
    const { state, velocityX, velocityY, absoluteX, absoluteY } = event.nativeEvent;
    if (state === GestureState.BEGAN) {
      swipeStart.current = { x: absoluteX, y: absoluteY, time: Date.now() };
      lastVelocity.current = 0;
    }
    if (state === GestureState.END && swipeStart.current) {
      const dx = absoluteX - swipeStart.current.x;
      const dy = absoluteY - swipeStart.current.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      const duration = Date.now() - swipeStart.current.time;
      const speed = distance / (duration || 1); // px/ms
      const direction =
        Math.abs(dx) > Math.abs(dy)
          ? dx > 0
            ? 'right'
            : 'left'
          : dy > 0
          ? 'down'
          : 'up';
      const acceleration = (Math.sqrt(velocityX * velocityX + velocityY * velocityY) - lastVelocity.current) / (duration || 1);

      setSwipeDistances((prev) => [...prev, distance]);
      setSwipeDurations((prev) => [...prev, duration]);
      setSwipeSpeeds((prev) => [...prev, speed]);
      setSwipeDirections((prev) => [...prev, direction]);
      setSwipeAccelerations((prev) => [...prev, acceleration]);
      const data = {
        swipeDistances,
        swipeDurations,
        swipeSpeeds,
        swipeDirections,
        swipeAccelerations,
        holdTimes,
        flightTimes,
        backspaceRates,
        typingSpeeds,
      };
      socket.emit('send-features', { data: data, userID: user._id });

      // Print all data to terminal after each swipe
      setTimeout(printAllData, 0);

      lastVelocity.current = Math.sqrt(velocityX * velocityX + velocityY * velocityY);
      swipeStart.current = null;
    }
  }, [swipeDistances, swipeDurations, swipeSpeeds, swipeDirections, swipeAccelerations]);

  // --- Print All Data ---
  function printAllData() {
    console.log({
      swiping: {
        swipeDistances,
        swipeDurations,
        swipeSpeeds,
        swipeDirections,
        swipeAccelerations,
      },
      typing: {
        holdTimes,
        flightTimes,
        backspaceRates,
        typingSpeeds,
      },
    });
  }

  const handleSubmit = async () => {
    if (!accountNumber || !cardType || !cardNo) {
      Alert.alert('Error', 'Please fill all required fields.');
      return;
    }
    setCards([
      ...cards,
      {
        accountNumber,
        cardType,
        cardNo,
        expiry,
      },
    ]);
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