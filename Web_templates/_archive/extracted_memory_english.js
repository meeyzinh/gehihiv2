function onEnglishTemplateLevelChange() {
    resetEnglishTemplateBoxes();

    const detailBox = document.getElementById("englishTemplateDetail");
    if (detailBox) {
        detailBox.innerHTML = `<div style="opacity:0.6;">👉 Chọn giáo trình hoặc tình huống nhập vai để xem</div>`;
    }

    loadEnglishTemplateSelect("");
}

function renderEnglishTutorTopicsByLevel() {
    const levelEl = document.getElementById("englishTutorLevel");
    const topicEl = document.getElementById("englishTutorTopic");

    if (!levelEl || !topicEl) return;

    const level = String(levelEl.value || "starter").toLowerCase();
    const topics = ENGLISH_TOPICS_BY_LEVEL[level] || ENGLISH_TOPICS_BY_LEVEL.starter;

    const oldValue = topicEl.value;

    topicEl.innerHTML = topics.map(t => `
        <option value="${escapeHTML(t.value)}">${escapeHTML(t.label)}</option>
    `).join("");

    if (topics.some(t => t.value === oldValue)) {
        topicEl.value = oldValue;
    } else if (topics.length) {
        topicEl.value = topics[0].value;
    }
}

function onEnglishTutorLevelChange() {
    renderEnglishTutorTopicsByLevel();

    resetEnglishTemplateBoxes();

    const detailBox = document.getElementById("englishTemplateDetail");
    if (detailBox) {
        detailBox.innerHTML = `<div style="opacity:0.6;">👉 Chọn giáo trình hoặc tình huống nhập vai để xem</div>`;
    }

    loadEnglishTemplateSelect("");
}


function toggleEnglishTemplateBox(type) {
    const box = document.getElementById(
        type === "lesson" ? "englishLessonTemplateList" : "englishRoleplayTemplateList"
    );

    const icon = document.getElementById(
        type === "lesson" ? "icon-english-lesson" : "icon-english-roleplay"
    );

    if (!box || !icon) return;

    const isOpen = box.classList.contains("open");

    if (isOpen) {
        box.classList.remove("open");
        icon.style.transform = "rotate(0deg)";
    } else {
        box.classList.add("open");
        icon.style.transform = "rotate(90deg)";
    }
}

function resetEnglishTemplateBoxes() {
    const lessonBox = document.getElementById("englishLessonTemplateList");
    const roleplayBox = document.getElementById("englishRoleplayTemplateList");
    const lessonIcon = document.getElementById("icon-english-lesson");
    const roleplayIcon = document.getElementById("icon-english-roleplay");

    if (lessonBox) lessonBox.classList.remove("open");
    if (roleplayBox) roleplayBox.classList.remove("open");

    if (lessonIcon) lessonIcon.style.transform = "rotate(0deg)";
    if (roleplayIcon) roleplayIcon.style.transform = "rotate(0deg)";
}



async function applyEnglishTemplate(templateId) {
    if (!currentMemoryDevice) {
        alert("Chưa có thiết bị");
        return;
    }

    try {
        const res = await fetch("/api/english-tutor/activate-template", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + localStorage.getItem("token")
            },
            body: JSON.stringify({
                deviceId: currentMemoryDevice,
                templateId
            })
        });

        const data = await res.json().catch(() => ({}));

        if (!res.ok) {
            alert(data.error || "Không áp dụng được giáo trình");
            return;
        }

        currentEnglishTemplateId = templateId;

        alert("✅ Đã áp dụng giáo trình tiếng Anh. Hãy gọi Sophia để bắt đầu.");

        await loadActiveEnglishTutor();

        renderEnglishTemplateList("lesson");
        renderEnglishTemplateList("roleplay");

        const selected =
            englishLessonTemplates.find(x => x.id === templateId) ||
            englishRoleplayTemplates.find(x => x.id === templateId);

        if (selected) {
            const type = selected.mode === "roleplay" ? "roleplay" : "lesson";
            showEnglishTemplateDetail(selected, type);
        }

    } catch (err) {
        alert("Lỗi kết nối máy chủ");
    }
}

async function loadEnglishTemplateSelect(openType = "") {
    const lessonBox = document.getElementById("englishLessonTemplateList");
    const roleplayBox = document.getElementById("englishRoleplayTemplateList");
    const detailBox = document.getElementById("englishTemplateDetail");

    if (!lessonBox || !roleplayBox || !detailBox) return;

    lessonBox.innerHTML = `<div class="curriculum-item">⏳ Đang tải giáo trình...</div>`;
    roleplayBox.innerHTML = `<div class="curriculum-item">⏳ Đang tải tình huống...</div>`;

    detailBox.innerHTML = `<div style="opacity:0.6;">👉 Chọn giáo trình hoặc tình huống nhập vai để xem</div>`;

    try {
        const level = document.getElementById("englishTemplateLevel")?.value || "";

        const levelQuery = level
    ? `level=${encodeURIComponent(level)}&`
    : "";

const [lessonRes, roleplayRes] = await Promise.all([
    fetch(`/api/english-tutor/templates?${levelQuery}mode=lesson`, {
        headers: {
            "Authorization": "Bearer " + localStorage.getItem("token")
        }
    }),
    fetch(`/api/english-tutor/templates?${levelQuery}mode=roleplay`, {
        headers: {
            "Authorization": "Bearer " + localStorage.getItem("token")
        }
    })
]);

        const lessonData = await lessonRes.json().catch(() => ({}));
        const roleplayData = await roleplayRes.json().catch(() => ({}));

        if (!lessonRes.ok) {
            lessonBox.innerHTML = `<div class="curriculum-item">❌ ${escapeHTML(lessonData.error || "Không tải được giáo trình")}</div>`;
        } else {
            englishLessonTemplates = lessonData.templates || [];
            renderEnglishTemplateList("lesson");

            const lessonHeader = document.querySelector("[onclick=\"toggleEnglishTemplateBox('lesson')\"] span:first-child");
                if (lessonHeader) {
                lessonHeader.innerText = `📚 Giáo trình có sẵn (${englishLessonTemplates.length})`;
            }
        }

        if (!roleplayRes.ok) {
            roleplayBox.innerHTML = `<div class="curriculum-item">❌ ${escapeHTML(roleplayData.error || "Không tải được tình huống")}</div>`;
        } else {
            englishRoleplayTemplates = roleplayData.templates || [];
            renderEnglishTemplateList("roleplay");
            const roleplayHeader = document.querySelector("[onclick=\"toggleEnglishTemplateBox('roleplay')\"] span:first-child");
if (roleplayHeader) {
    roleplayHeader.innerText = `🎭 Tình huống nhập vai (${englishRoleplayTemplates.length})`;
}
        }

        if (openType === "lesson") {
    const box = document.getElementById("englishLessonTemplateList");
    const icon = document.getElementById("icon-english-lesson");

    if (box) box.classList.add("open");
    if (icon) icon.style.transform = "rotate(90deg)";
}

if (openType === "roleplay") {
    const box = document.getElementById("englishRoleplayTemplateList");
    const icon = document.getElementById("icon-english-roleplay");

    if (box) box.classList.add("open");
    if (icon) icon.style.transform = "rotate(90deg)";
}

    } catch (err) {
        lessonBox.innerHTML = `<div class="curriculum-item">❌ Lỗi kết nối máy chủ</div>`;
        roleplayBox.innerHTML = `<div class="curriculum-item">❌ Lỗi kết nối máy chủ</div>`;
    }
}

function renderEnglishTemplateList(type) {
    const box = document.getElementById(
        type === "lesson" ? "englishLessonTemplateList" : "englishRoleplayTemplateList"
    );

    if (!box) return;

    const list = type === "lesson"
        ? englishLessonTemplates
        : englishRoleplayTemplates;

    box.innerHTML = "";

    if (!list.length) {
        box.innerHTML = `
            <div class="curriculum-item">
                ${type === "lesson" ? "Chưa có giáo trình phù hợp" : "Chưa có tình huống nhập vai"}
            </div>
        `;
        return;
    }

    list
        .slice()
        .sort((a, b) => {
            const aActive = a.id === currentEnglishTemplateId ? -1 : 0;
            const bActive = b.id === currentEnglishTemplateId ? -1 : 0;

            if (aActive !== bActive) return aActive - bActive;

            const orderA = Number(a.order_no || 0);
            const orderB = Number(b.order_no || 0);

            if (orderA !== orderB) return orderA - orderB;

            return String(a.title || "").localeCompare(String(b.title || ""), "vi", {
                sensitivity: "base"
            });
        })
        .forEach(t => {
            const item = document.createElement("div");
            item.className = "curriculum-item";

            const isActive = t.id === currentEnglishTemplateId;

            if (isActive) {
                item.classList.add("active");
            }

            item.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
                    <span style="
                        flex:1;
                        min-width:0;
                        overflow:hidden;
                        text-overflow:ellipsis;
                        white-space:nowrap;
                    ">
                        ${type === "roleplay" ? "🎭 " : ""}${escapeHTML(t.title || "Bài tiếng Anh")}
                    </span>

                    ${isActive ? `
                        <span style="
                            color:#4ade80;
                            font-size:11px;
                            flex-shrink:0;
                            white-space:nowrap;
                        ">
                            ✔ Đang áp dụng
                        </span>
                    ` : ""}
                </div>
            `;

            item.onclick = (e) => showEnglishTemplateDetail(t, type, e);
            box.appendChild(item);
        });
}

function showEnglishTemplateDetail(t, type, e) {
    const container = document.getElementById("englishTemplateDetail");
    const card = document.getElementById("englishTemplateDetailCard");

    if (!container || !card) return;

    card.style.display = "block";

    const words = Array.isArray(t.target_words) ? t.target_words : [];
    const phrases = Array.isArray(t.target_phrases) ? t.target_phrases : [];

    const isRoleplay = type === "roleplay" || t.mode === "roleplay";
    const isActive = t.id === currentEnglishTemplateId;

    const wordsText = words.length
        ? words.map(w => `- ${w}`).join("\n")
        : "Chưa có";

    const phrasesText = phrases.length
        ? phrases.map(p => `- ${p}`).join("\n")
        : "Chưa có";

    container.innerHTML = `
        <div class="memory-item">

            <strong style="font-size:16px;">
                ${isRoleplay ? "🎭 " : "📚 "}
                ${escapeHTML(t.title || "Bài tiếng Anh")}
                ${isActive ? "<span style='color:#4ade80;font-size:12px;'> ✔ Đang áp dụng</span>" : ""}
            </strong>

            <div style="font-size:12px;opacity:0.7;margin-top:6px;">
                Level: ${escapeHTML(t.level || "starter")}
                · Chủ đề: ${escapeHTML(t.topic || "")}
                · Chế độ: ${isRoleplay ? "Đóng vai luyện nói" : "Bài học"}
            </div>

            ${isRoleplay ? `
                <div style="
                    margin-top:12px;
                    padding:12px;
                    border-radius:10px;
                    background:rgba(168,85,247,0.10);
                    border:1px solid rgba(216,180,254,0.18);
                    line-height:1.6;
                ">
                    <strong>🎭 Tình huống nhập vai</strong><br>
                    ${escapeHTML(t.scenario || "Chưa có tình huống")}
                </div>
            ` : ""}

            <div style="margin-top:12px; white-space:pre-line; line-height:1.6;">
                <strong>🎯 Từ trong bài</strong>
                ${escapeHTML(wordsText)}

                <strong>💬 Câu luyện nói</strong>
                ${escapeHTML(phrasesText)}
            </div>

            ${t.tutor_note ? `
                <div style="
                    margin-top:12px;
                    padding:12px;
                    border-radius:10px;
                    background:rgba(59,130,246,0.10);
                    border:1px solid rgba(96,165,250,0.18);
                    white-space:pre-line;
                    line-height:1.6;
                ">
                    <strong>📝 Ghi chú cho gia sư</strong><br>
                    ${escapeHTML(t.tutor_note)}
                </div>
            ` : ""}

            <div class="action-row" style="margin-top:12px;">
                <button class="primary" onclick="applyEnglishTemplate('${t.id}')">
                    ${isRoleplay ? "Áp dụng tình huống" : "Áp dụng giáo trình"}
                </button>

                <button class="secondary" onclick="loadActiveEnglishTutor()">
                    Tải bài đang áp dụng
                </button>
            </div>

        </div>
    `;

    document.querySelectorAll("#englishLessonTemplateList .curriculum-item, #englishRoleplayTemplateList .curriculum-item").forEach(el => {
        el.classList.remove("active");
    });

    e?.currentTarget?.classList?.add("active");

    if (window.innerWidth < 768) {
        setTimeout(() => {
            const detailCard = document.getElementById("englishTemplateDetailCard");
            if (detailCard) {
                detailCard.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });
            }
        }, 100);
    }
}

function getEnglishSessionStatusLabel(status) {
    if (status === "completed") return "✅ Đã hoàn thành";
    if (status === "started") return "🟡 Đang học";
    if (status === "abandoned") return "⚠️ Học dang dở";
    return status || "Không rõ";
}

async function loadEnglishTutorReport() {
    const box = document.getElementById("englishTutorReportBox");

    if (!currentMemoryDevice) {
        if (box) box.innerHTML = "Chưa có thiết bị";
        return;
    }

    try {
        if (box) box.innerHTML = "⏳ Đang tải báo cáo...";

        const res = await fetch(`/api/english-tutor/report?deviceId=${encodeURIComponent(currentMemoryDevice)}`, {
            headers: {
                "Authorization": "Bearer " + localStorage.getItem("token")
            }
        });

        const data = await res.json().catch(() => ({}));

        if (!res.ok) {
            if (box) box.innerHTML = escapeHTML(data.error || "Không tải được báo cáo");
            return;
        }

        const profile = data.profile || {};
        const stats = data.stats || {};
        const sessions = data.sessions || [];

        const recentHtml = sessions.slice(0, 5).map(s => {
    const startedAt = s.started_at
        ? new Date(s.started_at).toLocaleString("vi-VN")
        : new Date(s.created_at).toLocaleString("vi-VN");

    const targetWords = Array.isArray(s.target_words) ? s.target_words : [];
    const targetPhrases = Array.isArray(s.target_phrases) ? s.target_phrases : [];

    const learnedWords = Array.isArray(s.learned_words) ? s.learned_words : [];
    const weakWords = Array.isArray(s.weak_words) ? s.weak_words : [];

    const isCompleted = s.status === "completed";

    return `
📘 ${escapeHTML(s.lesson_title || "Bài học tiếng Anh")}
- Trạng thái: ${escapeHTML(getEnglishSessionStatusLabel(s.status))}
- Chủ đề: ${escapeHTML(s.topic || "")}
- Chế độ: ${escapeHTML(s.mode || "lesson")}
- Bắt đầu: ${escapeHTML(startedAt)}
- Thời lượng: ${Math.round((s.duration_seconds || 0) / 60)} phút
- Điểm: ${isCompleted ? `${s.score || 0}/100` : "Chưa chấm"}
- Từ trong bài: ${escapeHTML(targetWords.join(", ") || "Chưa có")}
- Câu luyện nói: ${escapeHTML(targetPhrases.join(", ") || "Chưa có")}
- Bé đã nói được: ${escapeHTML(learnedWords.join(", ") || (isCompleted ? "Chưa có" : "Chưa ghi nhận"))}
- Cần luyện thêm: ${escapeHTML(weakWords.join(", ") || "Chưa có")}
- Nhận xét: ${escapeHTML(decodeHtmlEntities(s.summary || ""))}
`;
}).join("\n----------------------\n");

        const reportText = `
📊 TỔNG QUAN
- Tổng buổi học: ${stats.total_sessions || 0}
- Đã hoàn thành: ${stats.completed_sessions || 0}
- Học dang dở: ${stats.abandoned_sessions || 0}
- Đang học: ${stats.started_sessions || 0}
- Tổng thời gian: ${Math.round((stats.total_seconds || 0) / 60)} phút
- Điểm trung bình: ${stats.avg_score || 0}/100
- Chuỗi ngày học: ${profile.streak_days || 0} ngày

🎯 HỒ SƠ HIỆN TẠI
- Trình độ: ${profile.level || "starter"}
- Chủ đề gần nhất: ${profile.last_topic || "Chưa có"}
- Bài gần nhất: ${profile.last_lesson_title || "Chưa có"}

✅ TỪ ĐÃ BIẾT
${(profile.known_words || []).join(", ") || "Chưa có"}

⚠️ TỪ CẦN ÔN
${(profile.weak_words || []).join(", ") || "Chưa có"}

📝 5 BUỔI GẦN NHẤT
${recentHtml || "Chưa có buổi học nào"}
        `.trim();

        if (box) box.innerHTML = escapeHTML(reportText);

    } catch (err) {
        if (box) box.innerHTML = "Lỗi kết nối máy chủ";
    }
}

async function deleteActiveEnglishTutor() {
    if (!currentMemoryDevice) {
        setEnglishTutorMessage("error", "Chưa có thiết bị");
        return;
    }

    if (!confirm("Tắt chế độ học tiếng Anh đang áp dụng?")) return;

    try {
        const res = await fetch("/api/english-tutor/active", {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + localStorage.getItem("token")
            },
            body: JSON.stringify({
                deviceId: currentMemoryDevice
            })
       