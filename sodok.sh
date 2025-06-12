#!/bin/bash

# =================================================================
# Sincan2 Interactive Runner
# Author: MHL TEAM
# Version: 4.0 (Stable Interactive & Batch Modes)
# Deskripsi: Menjalankan sincan2.py dengan logika yang benar untuk
#            setiap mode, memperbaiki bug shell dan input.
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
    echo -e "${YELLOW}================= SINCAN2 RUNNER MENU ===================${NC}"
    echo -e ""
    echo -e "  ${CYAN}[1]${NC} 🎯  Pindai Target Tunggal (Interaktif)"
    echo -e "  ${CYAN}[2]${NC} 📂  Pindai Massal & Masuk Shell (Berhenti di tiap sukses)"
    echo -e "  ${CYAN}[3]${NC} 🚀  ${GREEN}Pindai Massal & Kumpulkan Hasil (Non-Interaktif)${NC}"
    echo -e ""
    echo -e "  ${RED}[4]${NC} 🚪  Keluar"
    echo -e ""
    echo -e "${YELLOW}===========================================================${NC}"
}

# --- Fungsi untuk mem-parsing output dan menyimpan hasil (HANYA UNTUK MODE BATCH) ---
function parse_and_save_results() {
    local output="$1"
    local shell_success_file="berhasil.txt"
    local potential_url_file="targeturl.txt"
    
    # Dapatkan base URL dari header output, ini adalah sumber utama
    base_url=$(echo "$output" | grep "Memeriksa Host:" | awk '{print $4}')

    # --- Logika untuk menyimpan ke berhasil.txt ---
    if echo "$output" | grep -q "\[ SUCCESS \]"; then
        if ! grep -q -x -F -- "$base_url" "$shell_success_file" 2>/dev/null; then
            echo "$base_url" >> "$shell_success_file"
            echo -e "${GREEN}🎉 [Target Sukses] Disimpan ke '$shell_success_file': $base_url${NC}"
        fi
    fi

    # --- Logika untuk menyimpan ke targeturl.txt ---
    echo "$output" | grep "└─>" | while read -r line ; do
        url=$(echo "$line" | awk '{print $NF}')
        echo "$url" >> "$potential_url_file"
        echo -e "${GREEN}🎉 https://dictionary.cambridge.org/dictionary/norwegian-english/potensial Disimpan ke '$potential_url_file': $url${NC}"
    done
}

# --- Fungsi untuk Opsi Massal ---
function mass_scan_logic() {
    local mode=$1 # 'interactive' atau 'batch'
    local filename port timeout=2 extra_flags=""
    
    echo -e "\n--- 📂 Pindai Massal dari File ---"
    read -p "  Masukkan nama file list IP (contoh: koped.txt): " filename
    if [[ -z "$filename" ]]; then echo -e "${RED}Error: Nama file tidak boleh kosong!${NC}"; sleep 2; return; fi
    if [ ! -f "$filename" ]; then echo -e "${RED}Error: File '$filename' tidak ditemukan!${NC}"; sleep 2; return; fi
    read -p "  Masukkan port yang akan digunakan untuk semua IP (opsional jika URL lengkap di file): " port
    read -p "  ⏱️  Berapa lama timeout? (default: 2 detik, tekan enter): " user_timeout
    timeout=${user_timeout:-2}
    read -p "  🔬  Aktifkan pemindaian modern (CVE)? (y/n, default: y): " modern_scan
    if [[ ! "$modern_scan" =~ ^[Nn]$ ]]; then extra_flags+=" -M"; fi

    extra_flags+=" --auto-exploit"
    if [[ "$mode" == "batch" ]]; then
        extra_flags+=" --batch-mode"
        echo -e "${GREEN}Mode 'Pindai & Lanjut' diaktifkan. Tidak akan masuk ke shell interaktif.${NC}"
    fi

    # PERBAIKAN UTAMA: Membaca file ke dalam array SEBELUM loop untuk mencegah pembajakan stdin
    mapfile -t all_lines < <(tr -d '\r' < "$filename")

    total_ips=${#all_lines[@]}
    if [ "$total_ips" -eq 0 ]; then echo -e "\n${YELLOW}⚠️ File '$filename' kosong.${NC}"; sleep 2; return; fi
    
    echo -e "\n${GREEN}🔍 Siap memindai ${total_ips} IP/URL dari file '${filename}'${NC}"
    echo -e "Tekan [ENTER] untuk memulai..."
    read
    
    local processed_count=0
    # Loop melalui array, bukan membaca dari file secara langsung
    for line_raw in "${all_lines[@]}"; do
        line=$(echo -n "$line_raw" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
        if [[ -z "$line" ]]; then continue; fi

        ((processed_count++))
        local target_url
        if [[ "$line" =~ ^https?:// ]]; then
            target_url="$line"
        else
            if [[ -z "$port" ]]; then echo -e "${RED}Error: Port wajib diisi untuk IP '$line'. Lanjut...${NC}"; sleep 1; continue; fi
            target_url="http://$line:$port"
        fi

        local final_command="python3 ./sincan2.py -u \"$target_url\" --timeout $timeout$extra_flags"
        
        echo -e "\n${BLUE}===========================================================${NC}"
        echo -e "${CYAN}[$processed_count/$total_ips] Memindai target: $target_url${NC}"
        echo -e "${BLUE}===========================================================${NC}"

        # Sekarang logika ini aman untuk kedua mode
        if [[ "$mode" == "batch" ]]; then
            scan_output=$(eval "$final_command" | tee /dev/tty)
            parse_and_save_results "$scan_output"
        else
            eval "$final_command"
        fi
        
        # Hapus baris yang sudah diproses dari file asli menggunakan grep yang lebih aman
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
               # Jalankan langsung untuk mode interaktif
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
