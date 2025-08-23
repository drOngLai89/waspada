import React from 'react';
import { ScrollView, View, Text, Linking, TouchableOpacity } from 'react-native';

const H1 = ({ children }: { children: React.ReactNode }) => (
  <Text style={{ color: '#E8ECF3', fontSize: 24, fontWeight: '700', marginBottom: 8 }}>{children}</Text>
);
const H2 = ({ children }: { children: React.ReactNode }) => (
  <Text style={{ color: '#C9D7F3', fontSize: 18, fontWeight: '700', marginTop: 18, marginBottom: 6 }}>{children}</Text>
);
const P = ({ children }: { children: React.ReactNode }) => (
  <Text style={{ color: '#A8B7D9', fontSize: 15, lineHeight: 22, marginBottom: 8 }}>{children}</Text>
);
const Bullet = ({ children }: { children: React.ReactNode }) => (
  <View style={{ flexDirection: 'row', marginBottom: 6 }}>
    <Text style={{ color: '#A8B7D9', marginRight: 8 }}>{'\u2022'}</Text>
    <Text style={{ color: '#A8B7D9', flex: 1, lineHeight: 22 }}>{children}</Text>
  </View>
);
const LinkText = ({ href, children }: { href: string; children: React.ReactNode }) => (
  <Text
    style={{ color: '#6EA8FE', textDecorationLine: 'underline' }}
    onPress={() => Linking.openURL(href)}
  >
    {children}
  </Text>
);
const Tel = ({ number, label }: { number: string; label?: string }) => (
  <TouchableOpacity onPress={() => Linking.openURL(`tel:${number.replace(/[^+\d]/g, '')}`)}>
    <Text style={{ color: '#6EA8FE' }}>{label ? `${label}: ` : ''}{number}</Text>
  </TouchableOpacity>
);

export default function HelpScreen() {
  return (
    <ScrollView style={{ flex: 1, backgroundColor: '#0B1220' }} contentContainerStyle={{ padding: 16 }}>
      <H1>Welcome to Berani</H1>
      <P>
        Berani helps you record incidents of bullying, harassment, domestic violence, or cyber harm in a calm,
        structured way—so you can keep clear notes, attach photos, and share a clean report when you choose.
        Your story is yours. Berani is built to help you document it safely and clearly.
      </P>

      <H2>Why use Berani (vs. WhatsApp or plain notes)?</H2>
      <Bullet>Structured fields (category, date/time pickers, location, photos) make records consistent and easy to review.</Bullet>
      <Bullet>AI drafting converts your points into a neutral, respectful report you can edit before sharing.</Bullet>
      <Bullet>“Vault” saves to your device, so you can keep drafts private until you decide to share.</Bullet>
      <Bullet>One-tap sharing exports your report (with photos) to email, messages, or other channels you trust.</Bullet>
      <Bullet>Designed to reduce re-telling: keep facts in one place, then reuse or print when needed.</Bullet>

      <H2>How Berani works (quick guide)</H2>
      <Bullet><Text style={{ fontWeight: '700', color: '#C9D7F3' }}>New Report</Text>: choose a category, set the correct date & time (use the pickers), add a location and photos, then write a short description.</Bullet>
      <Bullet><Text style={{ fontWeight: '700', color: '#C9D7F3' }}>AI Report</Text>: tap “Generate” to turn your notes into a clean report. Always review and edit to ensure accuracy.</Bullet>
      <Bullet><Text style={{ fontWeight: '700', color: '#C9D7F3' }}>Save to Vault</Text>: stores a copy locally on your phone. You can revisit and update later.</Bullet>
      <Bullet><Text style={{ fontWeight: '700', color: '#C9D7F3' }}>Share</Text>: send to trusted contacts, support organisations, or yourself for safekeeping.</Bullet>

      <H2>Tips & tricks for strong reports</H2>
      <Bullet>Stick to facts: who, what, when, where. Avoid labelling or assumptions.</Bullet>
      <Bullet>Use exact times if possible; if unsure, say “about 11:40am”.</Bullet>
      <Bullet>Photos: include clear context (scene, damage, injuries, messages). Remove any you added by mistake.</Bullet>
      <Bullet>Locations: use “Use current” for GPS, or type a known place (school, building, street).</Bullet>
      <Bullet>Keep identifying details (names, phone numbers, vehicle plates) if they are relevant and safe to include.</Bullet>
      <Bullet>After saving to the Vault, consider exporting a copy to a secure personal email for backup.</Bullet>

      <H2>Safety & privacy notes</H2>
      <Bullet><Text style={{ fontWeight: '700', color: '#C9D7F3' }}>Emergency first</Text>: if anyone is in immediate danger, call <Text style={{ color: '#E8ECF3', fontWeight: '700' }}>999</Text> (or <Text style={{ color: '#E8ECF3', fontWeight: '700' }}>112</Text> from mobile) right away.</Bullet>
      <Bullet>Reports saved in the Vault stay on your device until you share them. AI features send your typed text to our server to generate wording. If you prefer not to transmit anything, skip AI and save your manual notes.</Bullet>
      <Bullet>Consider setting a phone passcode/biometrics and hiding notifications for extra privacy.</Bullet>

      <H2>When to seek professional help</H2>
      <Bullet>If you feel unsafe, threatened, stalked, or controlled by someone.</Bullet>
      <Bullet>If there are injuries or medical concerns.</Bullet>
      <Bullet>If the harm involves a child or vulnerable person.</Bullet>
      <Bullet>If you’re distressed, anxious, or having trouble coping—please reach out for support.</Bullet>

      <H2>Malaysia hotlines & support</H2>
      <P>Numbers can change—if a line doesn’t connect, try again later or dial <Text style={{ color: '#E8ECF3', fontWeight: '700' }}>999</Text>.</P>

      <H2>Emergency</H2>
      <Bullet><Text style={{ fontWeight: '700', color: '#C9D7F3' }}>MERS 999</Text> – Police / Ambulance / Fire. <Tel number="999" /></Bullet>

      <H2>Domestic violence / family support</H2>
      <Bullet>
        <Text style={{ fontWeight: '700', color: '#C9D7F3' }}>Talian Kasih 15999 (24/7, KPWKM)</Text>{'\n'}
        Hotline <Tel number="15999" /> • WhatsApp <Tel number="+60 19-261 5999" />
      </Bullet>
      <Bullet>
        <Text style={{ fontWeight: '700', color: '#C9D7F3' }}>Women’s Aid Organisation (WAO)</Text>{'\n'}
        Hotline <Tel number="+60 3-3000 8858" /> • WhatsApp TINA <Tel number="+60 18-988 8058" /> • <LinkText href="https://wao.org.my/contact-us/">More info</LinkText>
      </Bullet>
      <Bullet>
        <Text style={{ fontWeight: '700', color: '#C9D7F3' }}>AWAM – All Women’s Action Society</Text>{'\n'}
        Helpline <Tel number="+60 3-2266 2222" /> • Office <Tel number="+60 3-7877 4221" /> • <LinkText href="https://www.awam.org.my/contact-us-2/">Contact</LinkText>
      </Bullet>

      <H2>Emotional support</H2>
      <Bullet>
        <Text style={{ fontWeight: '700', color: '#C9D7F3' }}>Befrienders Kuala Lumpur (24/7)</Text>{'\n'}
        <Tel number="+60 3-7627 2929" /> • Email <LinkText href="mailto:sam@befrienders.org.my">sam@befrienders.org.my</LinkText> • <LinkText href="https://www.befrienders.org.my/contact">More info</LinkText>
      </Bullet>

      <H2>Cyberbullying / online harms</H2>
      <Bullet>
        <Text style={{ fontWeight: '700', color: '#C9D7F3' }}>Cyber999 (MyCERT / CyberSecurity Malaysia)</Text>{'\n'}
        Hotline <Tel number="1-300-88-2999" /> • 24/7 Emergency <Tel number="+60 19-266 5850" /> • <LinkText href="https://www.mycert.org.my/cyber999">Report online</LinkText>
      </Bullet>

      <H2>Good to know</H2>
      <Bullet>You can draft reports offline; sharing requires connectivity.</Bullet>
      <Bullet>Keep your device charged; consider enabling automatic photo backup (if it’s safe for you).</Bullet>
      <Bullet>If you’re a student, you may share reports with a trusted teacher, counselor, or parent/guardian.</Bullet>

      <View style={{ height: 24 }} />
    </ScrollView>
  );
}
