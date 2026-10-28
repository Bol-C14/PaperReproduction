; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(assert
 (let ((?x934 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) c)))))))))
(let ((?x179 ((_ zero_extend 2) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) b)))))))))
(let ((?x23 (bvmul ?x179 ((_ zero_extend 3) ((_ extract 1 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) a)))))))))
(let ((?x11 ((_ zero_extend 1) ((_ extract 4 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ zero_extend 11) ?x23))))))))
(let (($x27 (and (distinct (ite (bvult a (_ bv4 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x71 ((_ extract 15 0) (bvmul ((_ extract 15 0) a) ((_ zero_extend 13) ((_ extract 2 0) b))))))
(and (distinct (ite $x27 (bvadd ?x71 ?x71) c) (ite $x27 ((_ zero_extend 10) (bvadd ?x11 ?x11)) ?x934)) true))))))))
(check-sat)
