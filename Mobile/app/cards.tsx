import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, TextInput, Alert, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { Feather, MaterialCommunityIcons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function CardsScreen() {
  const router = useRouter();
  const [accountNumber, setAccountNumber] = useState('');
  const [cardType, setCardType] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [cardNo, setCardNo] = useState('');
  const [pin, setPin] = useState('');
  const [cvv, setCvv] = useState('');
  const [expiry, setExpiry] = useState('');
  const [cards, setCards] = useState<any[]>([]);

  // Load cards from AsyncStorage on mount
  useEffect(() => {
    (async () => {
      const stored = await AsyncStorage.getItem('cards');
      if (stored) setCards(JSON.parse(stored));
    })();
  }, []);

  // Save cards to AsyncStorage whenever cards change
  useEffect(() => {
    AsyncStorage.setItem('cards', JSON.stringify(cards));
  }, [cards]);

  const handleSubmit = () => {
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
          onChangeText={setAccountNumber}
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
          onChangeText={setCardNo}
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
          onChangeText={setPin}
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
          onChangeText={setCvv}
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
          onChangeText={setExpiry}
        />
      </View>
      <TouchableOpacity style={styles.submitBtn} onPress={handleSubmit}>
        <Text style={styles.submitBtnText}>Submit</Text>
      </TouchableOpacity>
    </ScrollView>
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