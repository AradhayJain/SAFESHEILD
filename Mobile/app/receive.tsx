import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { Feather } from '@expo/vector-icons';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

export default function ReceiveScreen() {
  const router = useRouter();
  const [amount, setAmount] = useState('');
  const [note, setNote] = useState('');

  // Helper to handle text input changes (no behaviour tracking)
  const handleTyping = (text: string, _prevText: string, setText: (v: string) => void) => {
    setText(text);
  };

  const handleReceiveMoney = async () => {
    // You can add your receive logic here
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
          <Text style={styles.heading}>Receive Money</Text>

          {/* Amount Input */}
          <View style={styles.inputRow}>
            <TextInput
              style={styles.input}
              placeholder="Amount"
              value={amount}
              onChangeText={text => handleTyping(text, amount, setAmount)}
              keyboardType="numeric"
            />
          </View>

          {/* Note Input */}
          <View style={styles.inputRow}>
            <TextInput
              style={styles.input}
              placeholder="Note (Optional)"
              value={note}
              onChangeText={text => handleTyping(text, note, setNote)}
            />
          </View>

          {/* Receive Money Button */}
          <TouchableOpacity style={styles.receiveBtn} onPress={handleReceiveMoney}>
            <Text style={styles.receiveBtnText}>Receive Money</Text>
          </TouchableOpacity>

          {/* Info Text */}
          <Text style={styles.infoText}>
            Share your UPI ID to receive payments
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
  receiveBtn: {
    backgroundColor: '#1976D2',
    borderRadius: 12,
    marginTop: 8,
    width: '100%',
    height: 54,
    alignItems: 'center',
    justifyContent: 'center',
  },
  receiveBtnText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  infoText: {
    color: '#888',
    fontSize: 15,
    marginTop: 18,
    textAlign: 'center',
  },
});