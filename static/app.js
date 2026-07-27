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
                    
                    const newHistoryContainer = doc.getElementById('chat-history-container');
                    let currentHistoryContainer = document.getElementById('chat-history-container');
                    
                    if (newHistoryContainer) {
                        if (currentHistoryContainer) {
                            // AMBIL HANYA WRAPPER AI TERAKHIR DARI RESPONS SERVER
                            const newAiWrappers = newHistoryContainer.querySelectorAll('.ai-wrapper');
                            const latestAiWrapper = newAiWrappers[newAiWrappers.length - 1];

                            if (latestAiWrapper) {
                                if (currentHistoryContainer.lastElementChild) {
                                    currentHistoryContainer.lastElementChild.remove();
                                }
                                
                                currentHistoryContainer.appendChild(latestAiWrapper);
                                
                                const aiContent = latestAiWrapper.querySelector('.ai-content');
                                if (aiContent) {
                                    runTypewriterEffect(aiContent);
                                }
                            }
                        } else {
                            const contentArea = document.querySelector('.content-area');
                            if (contentArea) {
                                contentArea.appendChild(newHistoryContainer);
                                const allAiContents = newHistoryContainer.querySelectorAll('.ai-content');
                                if (allAiContents.length > 0) {
                                    const lastAiContent = allAiContents[allAiContents.length - 1];
                                    runTypewriterEffect(lastAiContent);
                                }
                            }
                        }
                    }

                    const newHistoryMenu = doc.querySelector('.sidebar-form .sidebar-menu');
                    const currentHistoryMenu = document.querySelector('.sidebar-form .sidebar-menu');
                    if (newHistoryMenu && currentHistoryMenu) {
                        currentHistoryMenu.innerHTML = newHistoryMenu.innerHTML;
                    }

                    const newPrefMenu = doc.querySelector('.pref-menu');
                    const currentPrefMenu = document.querySelector('.pref-menu');
                    if (newPrefMenu && currentPrefMenu) {
                        currentPrefMenu.innerHTML = newPrefMenu.innerHTML;
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
                    sendBtn.style.opacity = '1'; 
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

document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.sidebar');
    
    if (sidebar) {
        const savedScrollPosition = sessionStorage.getItem('sidebarScrollPosition');
        
        if (savedScrollPosition !== null) {
            sidebar.scrollTop = parseInt(savedScrollPosition, 10);
        }

        sidebar.addEventListener('scroll', function() {
            sessionStorage.setItem('sidebarScrollPosition', sidebar.scrollTop);
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

function showInlineEdit(btnElement) {
    const wrapper = btnElement.closest('.user-wrapper');
    const staticView = wrapper.querySelector('.static-msg-view');
    const editView = wrapper.querySelector('.edit-msg-view');
    const textarea = editView.querySelector('.inline-edit-textarea');

    staticView.style.display = 'none';
    editView.style.display = 'block';
    
    autoResizeTextarea(textarea);
    
    textarea.focus();
    textarea.setSelectionRange(textarea.value.length, textarea.value.length);
}

function cancelInlineEdit(btnElement) {
    const wrapper = btnElement.closest('.user-wrapper');
    const staticView = wrapper.querySelector('.static-msg-view');
    const editView = wrapper.querySelector('.edit-msg-view');
    const textarea = editView.querySelector('.inline-edit-textarea');
    const originalText = staticView.querySelector('.user-text-content').innerText;

    textarea.value = originalText;
    editView.style.display = 'none';
    staticView.style.display = 'block';
}

function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

async function submitInlineEdit(index, btnElement) {
    const wrapper = btnElement.closest('.user-wrapper');
    const editView = wrapper.querySelector('.edit-msg-view');
    const textarea = editView.querySelector('.inline-edit-textarea');
    const saveBtn = editView.querySelector('.btn-edit-save');
    const newText = textarea.value.trim();

    if (!newText) {
        alert('Pesan tidak boleh kosong');
        return;
    }

    const originalBtnText = saveBtn.innerHTML;
    saveBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>';
    saveBtn.disabled = true;

    try {
        const response = await fetch('/api/truncate_chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat_index: parseInt(index) })
        });

        if (response.ok) {
            const allUserWrappers = document.querySelectorAll('.user-wrapper');
            const allAiWrappers = document.querySelectorAll('.ai-wrapper');
            
            for (let i = index; i < allUserWrappers.length; i++) {
                if (allUserWrappers[i]) allUserWrappers[i].remove();
                if (allAiWrappers[i]) allAiWrappers[i].remove();
            }

            const messageInput = document.getElementById('messageInput');
            if (messageInput) {
                messageInput.value = newText;
                
                const chatForm = document.getElementById('chatForm');
                if (chatForm) {
                    const submitEvent = new Event('submit', { cancelable: true, bubbles: true });
                    chatForm.dispatchEvent(submitEvent);
                }
            }
        } else {
            console.error("Gagal memotong chat di server.");
            saveBtn.innerHTML = originalBtnText;
            saveBtn.disabled = false;
        }
    } catch (error) {
        console.error("Terjadi kesalahan jaringan:", error);
        saveBtn.innerHTML = originalBtnText;
        saveBtn.disabled = false;
    }
}

function toggleChatMenu(event, sessionId) {
    event.preventDefault(); 
    event.stopPropagation(); 
    
    document.querySelectorAll('.chat-options-menu').forEach(menu => {
        if (menu.id !== 'menu-' + sessionId) {
            menu.classList.remove('show');
        }
    });

    const targetMenu = document.getElementById('menu-' + sessionId);
    if (targetMenu) {
        targetMenu.classList.toggle('show');
    }
}

window.addEventListener('click', function(event) {
    if (!event.target.closest('.chat-item-options')) {
        document.querySelectorAll('.chat-options-menu').forEach(menu => {
            menu.classList.remove('show');
        });
    }
});

function renameChat(sessionId, currentTitle) {
    const newTitle = prompt("Masukkan nama baru untuk obrolan ini:", currentTitle);
    
    if (newTitle !== null && newTitle.trim() !== "" && newTitle !== currentTitle) {
        document.getElementById('rename_session_id').value = sessionId;
        document.getElementById('rename_new_title').value = newTitle.trim();
        
        document.getElementById('renameForm').submit();
    }
}

function openPaymentModal(productName, productPrice) {
    const modal = document.getElementById('paymentModal');
    
    document.getElementById('modalProductName').innerText = productName || 'Produk';
    document.getElementById('modalProductPrice').innerText = productPrice || 'Rp -';

    modal.style.display = 'flex'; 
    
    const statusDiv = document.getElementById('paymentStatus');
    if(statusDiv) statusDiv.style.display = 'none';

    const buttons = document.querySelectorAll('.btn-payment');
    buttons.forEach(btn => {
        btn.disabled = false;
        btn.style.backgroundColor = 'var(--bg-main)';
        btn.style.borderColor = 'var(--hover-bg)';
        btn.style.color = 'var(--text-primary)';
        
        if (btn.getAttribute('data-original-html')) {
            btn.innerHTML = btn.getAttribute('data-original-html');
        } else {
            btn.setAttribute('data-original-html', btn.innerHTML);
        }
    });
}

function closePaymentModal() {
    const modal = document.getElementById('paymentModal');
    if(modal) modal.style.display = 'none';
}

function processPayment(btnElement, method) {
    const allButtons = document.querySelectorAll('.btn-payment');
    
    const currentPrice = document.getElementById('modalProductPrice').innerText;
    
    allButtons.forEach(btn => btn.disabled = true);

    btnElement.innerHTML = '<i class="fas fa-circle-notch fa-spin" style="margin-right: 8px;"></i> Memproses...';
    btnElement.style.borderColor = 'var(--accent-color)';

    const statusDiv = document.getElementById('paymentStatus');
    statusDiv.style.display = 'block';
    statusDiv.style.color = 'var(--text-secondary)';
    statusDiv.innerHTML = `Sedang menghubungi penyedia layanan ${method}...`;

    setTimeout(() => {
        btnElement.innerHTML = '<i class="fas fa-check-circle" style="margin-right: 8px;"></i> Berhasil';
        btnElement.style.backgroundColor = 'rgba(76, 175, 80, 0.15)'; 
        btnElement.style.borderColor = '#4CAF50';
        btnElement.style.color = '#4CAF50';

        statusDiv.style.color = '#4CAF50';
        
        statusDiv.innerHTML = `✅ Pembayaran ${currentPrice} menggunakan ${method} berhasil!`;

        setTimeout(() => {
            closePaymentModal();
        }, 2500);

    }, 2000);
}

window.addEventListener('click', function(event) {
    const paymentModal = document.getElementById('paymentModal');
    if (event.target === paymentModal) {
        closePaymentModal();
    }
});