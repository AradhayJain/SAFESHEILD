import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { Feather } from '@expo/vector-icons';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

export default function TopUpScreen() {
  const router = useRouter();
  const [account, setAccount] = useState('');
  const [amount, setAmount] = useState('');

  // Helper to handle text input changes (no behaviour tracking)
  const handleTyping = (text: string, _prevText: string, setText: (v: string) => void) => {
    setText(text);
  };

  const handleTopUp = async () => {
    if (!account || !amount) {
      Alert.alert('Error', 'Please enter account number and amount.');
      return;
    }
    Alert.alert('Success', 'Top up done successfully!');
    setAccount('');
    setAmount('');
  };

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <KeyboardAvoidingView
        style={{ flex: 1, backgroundColor: '#f7fafd' }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <View style={styles.container}>
          {/* Back Button */}
          <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
            <Feather name="arrow-left" size={26} color="#222" />
          </TouchableOpacity>

          {/* Heading */}
          <Text style={styles.heading}>Top Up</Text>

          {/* Account Number Input */}
          <View style={styles.inputRow}>
            <TextInput
              style={styles.input}
              placeholder="Account Number"
              value={account}
              onChangeText={text => handleTyping(text, account, setAccount)}
              keyboardType="default"
            />
          </View>

          {/* Amount Input */}
          <View style={styles.inputRow}>
            <Text style={{ marginLeft: 10, marginRight: 6, fontSize: 18 }}>₹</Text>
            <TextInput
              style={[styles.input, { borderWidth: 0, marginLeft: 0 }]}
              placeholder="Amount"
              value={amount}
              onChangeText={text => handleTyping(text, amount, setAmount)}
              keyboardType="numeric"
            />
          </View>

          {/* Continue Button */}
          <TouchableOpacity style={styles.continueBtn} onPress={handleTopUp}>
            <Text style={styles.continueBtnText}>CONTINUE</Text>
          </TouchableOpacity>

          {/* Info Text */}
          <Text style={styles.infoText}>
            Top up a mobile number linked to your account
          </Text>
        </View>
      </KeyboardAvoidingView>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingTop: 60,
    paddingHorizontal: 18,
    backgroundColor: '#f7fafd',
    alignItems: 'center',
  },
  backBtn: {
    alignSelf: 'flex-start',
    marginBottom: 18,
    marginLeft: -6,
  },
  heading: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#222',
    marginBottom: 36,
    alignSelf: 'center',
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    marginBottom: 18,
    paddingHorizontal: 12,
    height: 56,
    width: '100%',
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: '#222',
    backgroundColor: 'transparent',
    borderWidth: 0,
  },
  continueBtn: {
    backgroundColor: '#1976D2',
    borderRadius: 12,
    marginTop: 8,
    width: '100%',
    height: 54,
    alignItems: 'center',
    justifyContent: 'center',
  },
  continueBtnText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    letterSpacing: 1,
  },
  infoText: {
    color: '#888',
    fontSize: 14,
    marginTop: 12,
    textAlign: 'center',
  },
});