import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons, MaterialIcons, Feather } from '@expo/vector-icons';

export default function MainScreen() {
  const router = useRouter();

  return (
    <View style={styles.outer}>
      <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
        <View style={styles.headerRow}>
          <View>
            <Text style={styles.greeting}>Good Morning, John</Text>
            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
              <MaterialCommunityIcons name="shield-check-outline" size={16} color="#2CC7A6" />
              <Text style={styles.status}> SafeShield Active </Text>
              <Text style={styles.percent}>5.6%</Text>
            </View>
          </View>
          <View style={styles.headerIcons}>
            <Feather name="bell" size={22} color="#244A85" style={{ marginRight: 16 }} />
            <Feather name="user" size={22} color="#244A85" onPress={() => router.push('/profile')} />
          </View>
        </View>

        <View style={styles.card}>
          <Text style={styles.balanceLabel}>Total Balance</Text>
          <Text style={styles.balance}>$24,853.42</Text>
          <Text style={styles.account}>Account: ****1234</Text>
          <Text style={styles.percentCard}>+2.4%</Text>
        </View>

        <View style={styles.row}>
          <TouchableOpacity
            style={styles.actionBtn}
            onPress={() => router.push('/send')}
          >
            <MaterialIcons name="arrow-upward" size={20} color="#2CC7A6" />
            <Text style={styles.actionText}>Send</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.actionBtn}
            onPress={() => router.push('/receive')}
          >
            <MaterialIcons name="arrow-downward" size={20} color="#2CC7A6" />
            <Text style={styles.actionText}>Receive</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.actionBtn}
            onPress={() => router.push('/top_up' as any)}
          >
            <MaterialIcons name="add" size={20} color="#2CC7A6" />
            <Text style={styles.actionText}>Top Up</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.shieldBox}>
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <MaterialCommunityIcons name="shield-outline" size={18} color="#2CC7A6" />
            <Text style={styles.shieldStatus}> SafeShield Status </Text>
            <Text style={styles.active}>• Active</Text>
          </View>
          <View style={styles.confidenceRow}>
            <View style={styles.confidenceCol}>
              <Text style={styles.confidenceValue}>11%</Text>
              <Text style={styles.confidenceLabel}>Touch Confidence</Text>
            </View>
            <View style={styles.confidenceCol}>
              <Text style={styles.confidenceValue}>12%</Text>
              <Text style={styles.confidenceLabel}>Gesture Match</Text>
            </View>
          </View>
        </View>

        <Text style={styles.sectionTitle}>Recent Activity</Text>
        <View style={styles.activityBox}>
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <MaterialCommunityIcons name="bank-transfer-in" size={22} color="#2CC7A6" />
            <Text style={styles.activityTitle}> Salary Deposit</Text>
          </View>
          <Text style={styles.activityAmount}>+ $3,500.00</Text>
          <Text style={styles.activityTime}>2 hours ago • Verified</Text>
        </View>
        <View style={styles.activityBox}>
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <MaterialCommunityIcons name="coffee" size={22} color="#e74c3c" />
            <Text style={styles.activityTitle}> Coffee Shop</Text>
          </View>
          <Text style={[styles.activityAmount, { color: '#e74c3c' }]}>- $4.50</Text>
          <Text style={styles.activityTime}>Yesterday • Auto-approved</Text>
        </View>

        {/* Profile navigation button */}
        {/* <TouchableOpacity 
          style={styles.profileBtn} 
          onPress={() => router.push('/profile')}
        >
          <Text style={styles.profileBtnText}>Go to Profile</Text>
        </TouchableOpacity> */}
      </ScrollView>

      {/* Bottom Navigation Bar */}
      <View style={styles.navBar}>
        <TouchableOpacity style={styles.navItem}>
          <MaterialCommunityIcons name="home-outline" size={24} color="#2CC7A6" />
          <Text style={styles.navLabelActive}>Home</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.navItem} onPress={() => router.push('/activity' as any)}>
          <MaterialCommunityIcons name="history" size={24} color="#b0b0b0" />
          <Text style={styles.navLabel}>Activity</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.navItem} onPress={() => router.push('/cards' as any)}>
          <MaterialCommunityIcons name="credit-card-outline" size={24} color="#b0b0b0" />
          <Text style={styles.navLabel}>Cards</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.navItem} onPress={() => router.push('/settings' as any)}>
          <MaterialCommunityIcons name="cog-outline" size={24} color="#b0b0b0" />
          <Text style={styles.navLabel}>Settings</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  outer: { flex: 1, backgroundColor: '#f7fafd' },
  container: { flex: 1, paddingHorizontal: 16, marginBottom: 70 },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 32, marginBottom: 12 },
  greeting: { fontSize: 22, fontWeight: 'bold', color: '#244A85' },
  status: { fontSize: 15, color: '#244A85' },
  percent: { color: '#2CC7A6', fontWeight: 'bold' },
  headerIcons: { flexDirection: 'row', alignItems: 'center' },
  card: { backgroundColor: '#2CC7A6', borderRadius: 18, padding: 24, marginBottom: 18, elevation: 2 },
  balanceLabel: { color: '#fff', fontSize: 14, marginBottom: 6 },
  balance: { color: '#fff', fontSize: 32, fontWeight: 'bold' },
  account: { color: '#e0f7ef', fontSize: 13, marginTop: 4 },
  percentCard: { color: '#fff', fontSize: 13, marginTop: 2 },
  row: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 18 },
  actionBtn: { flex: 1, backgroundColor: '#fff', margin: 4, borderRadius: 10, padding: 14, alignItems: 'center', flexDirection: 'row', justifyContent: 'center', borderWidth: 1, borderColor: '#e0e0e0' },
  actionText: { color: '#244A85', fontWeight: 'bold', marginLeft: 6 },
  shieldBox: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 18, elevation: 1 },
  shieldStatus: { fontWeight: 'bold', color: '#244A85', marginLeft: 6 },
  active: { color: '#2CC7A6', fontWeight: 'bold', marginLeft: 6 },
  confidenceRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 12 },
  confidenceCol: { alignItems: 'center', flex: 1 },
  confidenceValue: { color: '#2CC7A6', fontWeight: 'bold', fontSize: 18 },
  confidenceLabel: { color: '#b0b0b0', fontSize: 13, marginTop: 2 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', marginBottom: 8, color: '#244A85' },
  activityBox: { backgroundColor: '#fff', borderRadius: 10, padding: 14, marginBottom: 10, elevation: 1 },
  activityTitle: { fontWeight: 'bold', color: '#244A85', marginLeft: 6 },
  activityAmount: { color: '#2CC7A6', fontWeight: 'bold', fontSize: 16, marginTop: 4 },
  activityTime: { color: '#b0b0b0', fontSize: 12, marginTop: 2 },
  profileBtn: { backgroundColor: '#244A85', borderRadius: 8, padding: 14, alignItems: 'center', marginVertical: 24 },
  profileBtnText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
  navBar: { position: 'absolute', left: 0, right: 0, bottom: 0, backgroundColor: '#fff', flexDirection: 'row', height: 64, borderTopLeftRadius: 18, borderTopRightRadius: 18, elevation: 10, justifyContent: 'space-around', alignItems: 'center' },
  navItem: { alignItems: 'center', flex: 1 },
  navLabel: { color: '#b0b0b0', fontSize: 12, marginTop: 2 },
  navLabelActive: { color: '#2CC7A6', fontWeight: 'bold', fontSize: 12, marginTop: 2 },
});
