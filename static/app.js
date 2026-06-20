let isSubmitting = false;

function scrollToBottom() {
    const bottomDiv = document.getElementById('bottom-of-chat');

    if (bottomDiv) {
        bottomDiv.scrollIntoView({
            behavior: 'smooth',
            block: 'end'
        });
    }
}

function showLoadingVisuals(userText) {
    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn) {
        sendBtn.disabled = true;
        sendBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>'; 
    }

    let historyContainer = document.getElementById('chat-history-container');
    const welcomeContainer = document.querySelector('.welcome-container');

    if (welcomeContainer) welcomeContainer.style.display = 'none';

    if (!historyContainer) {
        historyContainer = document.createElement('div');
        historyContainer.id = 'chat-history-container';
        historyContainer.className = 'chat-history-container';
        const contentArea = document.querySelector('.content-area');
        if (contentArea) contentArea.appendChild(historyContainer);
    }

    if (userText && userText.trim() !== '') {
        const userBubble = `
            <div class="chat-wrapper user-wrapper" style="opacity: 0.7;">
                <div class="chat-message user-message">${userText}</div>
            </div>
        `;
        historyContainer.insertAdjacentHTML('beforeend', userBubble);
    }

    const loadingBubble = `
        <div class="chat-wrapper ai-wrapper">
            <div class="chat-message ai-message">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        </div>
    `;
    historyContainer.insertAdjacentHTML('beforeend', loadingBubble);

    scrollToBottom();
}

function triggerSmartRecommendation(btnElement) {
    if (isSubmitting) return;
    isSubmitting = true;
    
    btnElement.disabled = true;
    btnElement.innerHTML = '<i class="fas fa-circle-notch fa-spin" style="color: var(--accent-color);"></i> Memproses...';
    btnElement.style.opacity = '0.7';

    const messageInput = document.getElementById('messageInput');
    const textToSubmit = 'Beri saya rekomendasi produk yang cocok berdasarkan obrolan kita sejauh ini';
    
    if (messageInput) {
        messageInput.value = textToSubmit;
    }

    showLoadingVisuals(textToSubmit);

    const chatForm = document.getElementById('chatForm');
    if (chatForm) {
        chatForm.submit(); 
    }
}

function handleChatImagePreview(event) {
    const input = event.target; 
    const previewContainer = document.getElementById('chat_preview_container'); 
    const previewImage = document.getElementById('chat_preview_img'); 
    const removeBtn = document.getElementById('remove_chat_img_btn');
    const wrapper = previewContainer.querySelector('.preview-wrapper');

    if (input.files && input.files[0]) {
        const file = input.files[0];

        if (file.type.startsWith('image/')) {
            previewContainer.style.display = 'block';
            previewImage.style.display = 'none';
            if (removeBtn) removeBtn.style.display = 'none';

            let loadingSpinner = document.getElementById('preview_loading_spinner');
            if (!loadingSpinner) {
                loadingSpinner = document.createElement('div');
                loadingSpinner.id = 'preview_loading_spinner';
                loadingSpinner.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>';
                wrapper.prepend(loadingSpinner);
            } else {
                loadingSpinner.style.display = 'flex';
            }

            const reader = new FileReader();

            reader.onload = function(e) {
                setTimeout(() => {
                    if (loadingSpinner) loadingSpinner.style.display = 'none';
                    
                    previewImage.src = e.target.result;
                    previewImage.style.display = 'block';
                    
                    if (removeBtn) removeBtn.style.display = 'flex'; 
                }, 600);
            };

            reader.readAsDataURL(file);
        } else {
            alert("Harap pilih file gambar.");
            input.value = ""; 
        }
    } else {
        previewContainer.style.display = 'none';
    }
}

function removeChatImage() {
    const input = document.getElementById('file-upload');
    const previewContainer = document.getElementById('chat_preview_container');
    
    input.value = "";
    previewContainer.style.display = 'none';
}

document.addEventListener('DOMContentLoaded', function() {
    const chatFileInput = document.getElementById('file-upload');
    if (chatFileInput) {
        chatFileInput.addEventListener('change', handleChatImagePreview);
    }

    const removeBtn = document.getElementById('remove_chat_img_btn');
    if (removeBtn) {
        removeBtn.addEventListener('click', removeChatImage);
    }

    const chatForm = document.getElementById('chatForm');
    if (chatForm) {
        chatForm.addEventListener('submit', async function(event) {
            event.preventDefault(); 
            
            if (isSubmitting) return;
            isSubmitting = true; 
            
            const messageInput = document.getElementById('messageInput');
            const userText = messageInput ? messageInput.value : '';
            
            showLoadingVisuals(userText);
            
            const formData = new FormData(chatForm);
            
            if (messageInput) messageInput.value = '';
            removeChatImage();

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const htmlText = await response.text();
                    
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(htmlText, 'text/html');
                    
                    const newAiWrappers = doc.querySelectorAll('.ai-wrapper');
                    const latestAiWrapper = newAiWrappers[newAiWrappers.length - 1];

                    if (latestAiWrapper) {
                        const historyContainer = document.getElementById('chat-history-container');
                        
                        if (historyContainer && historyContainer.lastElementChild) {
                            historyContainer.lastElementChild.remove();
                        }
                        
                        historyContainer.appendChild(latestAiWrapper);
                        
                        const aiContent = latestAiWrapper.querySelector('.ai-content');
                        if (aiContent) {
                            runTypewriterEffect(aiContent);
                        }
                    }
                } else {
                    console.error("Gagal menghubungi server.");
                }
            } catch (error) {
                console.error("Terjadi kesalahan:", error);
            } finally {
                isSubmitting = false;
                const sendBtn = document.getElementById('sendBtn');
                if (sendBtn) {
                    sendBtn.disabled = false;
                    sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
                }
            }
        });
    }

    const aiContents = document.querySelectorAll('.ai-content');
    if (aiContents.length > 0) {
        const lastAiContent = aiContents[aiContents.length - 1];
        runTypewriterEffect(lastAiContent);
    }

    const toggleSidebarBtn = document.getElementById('toggleSidebarBtn');
    if (toggleSidebarBtn) {
        toggleSidebarBtn.addEventListener('click', function() {
            document.body.classList.toggle('sidebar-closed');
        });
    }
    
});

function runTypewriterEffect(aiContentElement) {
    const aiWrapper = aiContentElement.closest('.ai-wrapper');
    const evalMetrics = aiWrapper ? aiWrapper.querySelector('.eval-metrics') : null;
    const usabilityFeedback = aiWrapper ? aiWrapper.querySelector('.usability-feedback') : null;
    
    if (evalMetrics) evalMetrics.style.opacity = '0';
    if (usabilityFeedback) usabilityFeedback.style.opacity = '0';

    const originalHTML = aiContentElement.innerHTML; 
    aiContentElement.innerHTML = ''; 

    const tokens = originalHTML.match(/(<[^>]+>)|([^<]+)/g) || [];
    
    let tokenIndex = 0;
    let charIndex = 0;
    let currentHTML = ''; 
    const typingSpeed = 10; 
    let isTyping = true; 

    function scrollToBottom() {
        window.scrollTo({
            top: document.documentElement.scrollHeight,
            behavior: 'auto' 
        });
    }

    function isNearBottom() {
        const totalHeight = document.documentElement.scrollHeight;
        const currentScroll = window.scrollY || window.pageYOffset || document.documentElement.scrollTop;
        const windowHeight = window.innerHeight;
        return (totalHeight - currentScroll - windowHeight) <= 150;
    }

    let autoScrollEnabled = isNearBottom();

    function detectUserScrollIntent() {
        if (!isTyping) return;
        autoScrollEnabled = isNearBottom();
    }

    window.addEventListener('wheel', detectUserScrollIntent, { passive: true });
    window.addEventListener('touchmove', detectUserScrollIntent, { passive: true });

    function typeWriterSafe() {
        if (tokenIndex < tokens.length) {
            const currentToken = tokens[tokenIndex];

            if (currentToken.startsWith('<')) {
                currentHTML += currentToken;
                aiContentElement.innerHTML = currentHTML;
                tokenIndex++;
                if (autoScrollEnabled) scrollToBottom(); 
                typeWriterSafe();
            } else {
                if (charIndex < currentToken.length) {
                    currentHTML += currentToken.charAt(charIndex);
                    aiContentElement.innerHTML = currentHTML;
                    charIndex++;
                    if (autoScrollEnabled) scrollToBottom(); 
                    setTimeout(typeWriterSafe, typingSpeed);
                } else {
                    charIndex = 0;
                    tokenIndex++;
                    typeWriterSafe();
                }
            }
        } else {
            isTyping = false; 
            window.removeEventListener('wheel', detectUserScrollIntent);
            window.removeEventListener('touchmove', detectUserScrollIntent);

            if (evalMetrics) {
                evalMetrics.style.transition = 'opacity 0.5s ease-in';
                evalMetrics.style.opacity = '1';
            }
            if (usabilityFeedback) {
                usabilityFeedback.style.transition = 'opacity 0.5s ease-in';
                usabilityFeedback.style.opacity = '1';
            }
            if (autoScrollEnabled) {
                window.scrollTo({
                    top: document.documentElement.scrollHeight,
                    behavior: 'smooth'
                });
            }
        }
    }
    
    setTimeout(typeWriterSafe, 300);
}

function showPreferenceModal(title, contentData) {
    const modal = document.getElementById('prefModal');
    const modalTitle = document.getElementById('prefModalTitle');
    const modalBody = document.getElementById('prefModalBody');

    modalTitle.textContent = "Riwayat " + title;
    
    if (contentData && contentData !== 'Belum ada' && contentData !== 'Bebas') {
        const items = contentData.split(', ');
        
        let htmlList = '<ul style="padding-left: 20px; margin-top: 10px;">';
        items.forEach(item => {
            htmlList += `<li style="margin-bottom: 8px;"><strong>${item}</strong></li>`;
        });
        htmlList += '</ul>';
        
        modalBody.innerHTML = `<p>Berdasarkan obrolan sejauh ini, kami mendeteksi minatmu pada:</p> ${htmlList}`;
    } else {
        modalBody.innerHTML = `
            <p>Belum ada riwayat terdeteksi untuk <strong>${title}</strong>.</p>
            <p style="color: var(--text-secondary); font-size: 12px; margin-top: 15px;">
                <i class="fas fa-info-circle"></i> Mulai ngobrol dengan AI Agents UI agar kami bisa mengenali preferensimu!
            </p>
        `;
    }

    modal.style.display = 'flex'; 
}

function closePreferenceModal() {
    const modal = document.getElementById('prefModal');
    modal.style.display = 'none';
}

window.addEventListener('click', function(event) {
    const modal = document.getElementById('prefModal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
});

function sendFeedback(chatIndex, feedbackType, buttonElement) {
    let isAlreadyActive = false;
    if (feedbackType === 'up' && buttonElement.classList.contains('active-up')) {
        isAlreadyActive = true;
    } else if (feedbackType === 'down' && buttonElement.classList.contains('active-down')) {
        isAlreadyActive = true;
    }

    const finalFeedback = isAlreadyActive ? null : feedbackType;

    const data = {
        chat_index: parseInt(chatIndex),
        feedback: finalFeedback
    };

    fetch('/submit_feedback', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === 'success') {
            const feedbackContainer = buttonElement.parentElement;
            
            const allButtons = feedbackContainer.querySelectorAll('.feedback-btn');
            allButtons.forEach(btn => {
                btn.classList.remove('active-up', 'active-down');
            });
            
            if (!isAlreadyActive) {
                if (feedbackType === 'up') {
                    buttonElement.classList.add('active-up');
                } else if (feedbackType === 'down') {
                    buttonElement.classList.add('active-down');
                }
                console.log("✅ Usability feedback berhasil dicatat!");
            } else {
                console.log("❎ Usability feedback dibatalkan!");
            }
        } else {
            console.error("❌ Gagal menyimpan feedback:", result.message);
        }
    })
    .catch(error => {
        console.error("❌ Terjadi kesalahan jaringan saat mengirim feedback:", error);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const aiModeBtn = document.getElementById('aiModeBtn');
    const aiModeMenu = document.getElementById('aiModeMenu');
    
    if (aiModeBtn && aiModeMenu) {
        aiModeBtn.addEventListener('click', function(e) {
            e.stopPropagation(); 
            aiModeMenu.classList.toggle('show');
        });

        const dropdownItems = aiModeMenu.querySelectorAll('.dropdown-item');
        dropdownItems.forEach(item => {
            item.addEventListener('click', function(e) {
                e.stopPropagation();
                
                const type = this.getAttribute('data-type');
                const value = this.getAttribute('data-value');
                const label = this.getAttribute('data-label');
                
                aiModeMenu.querySelectorAll(`.dropdown-item[data-type="${type}"]`).forEach(el => {
                    el.classList.remove('active');
                });
                
                this.classList.add('active');
                
                if (type === 'source') {
                    document.getElementById('hidden_manual_source').value = value;
                } else if (type === 'algo') {
                    document.getElementById('hidden_manual_algo').value = value;
                    
                    if (label) {
                        aiModeBtn.querySelector('span').textContent = label;
                    }
                    
                    aiModeMenu.classList.remove('show'); 
                }
            });
        });

        window.addEventListener('click', function(e) {
            if (!aiModeMenu.contains(e.target) && e.target !== aiModeBtn) {
                aiModeMenu.classList.remove('show');
            }
        });
    }
});