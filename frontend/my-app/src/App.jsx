import { useState } from 'react';
import useAuth from './hooks/useAuth';
import useConversations from './hooks/useConversations';
import useChat from './hooks/useChat';

import Sidebar from './components/Sidebar';
import ConversationBlock from './components/ConversationBlock';
import Header from './components/Header';
import LoginPopup from './components/LoginPopup';
import LoadingScreen from './components/LoadingScreen';
import AdvertisementFooter from './components/AdvertisementFooter';

import './App.css'

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const auth = useAuth();
  const conversations = useConversations(auth.user);
  const chat = useChat({
    currentConversation: conversations.currentConversation,
    updateCurrentConversation: conversations.updateCurrentConversation,
    currentConversationId: conversations.currentConversationId,
  });

  if (auth.checkingAuth) {
    return <LoadingScreen />;
  }

  return (
    <div className={`app ${sidebarOpen ? '' : 'app--sidebar-collapsed'}`}>
      <div className="app__content">
        <Sidebar
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen((open) => !open)}
          conversations={conversations.conversations}
          currentConversationId={conversations.currentConversationId}
          onSelectConversation={conversations.selectConversation}
          onCreateConversation={conversations.createConversation}
        />

        <div className="app__main">
          <Header
            user={auth.user}
            onLoginClick={auth.openLogin}
            onLogout={auth.logout}
          />

          <ConversationBlock
            messages={conversations.currentConversation?.messages ?? []}
            loading={chat.loading}
            streaming={chat.streaming}
            onSendMessage={chat.sendMessage}
            onSuggestion={chat.sendPresetMessage}
          />
        </div>
      </div>

      <LoginPopup
        visible={auth.showLogin}
        onClose={auth.closeLogin}
        onLogin={auth.login}
        onSuccess={(user) => {
            auth.closeLogin();
            auth.refresh();
        }}
      />

      <AdvertisementFooter />
    </div>
  );
}
