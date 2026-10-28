; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(assert
 (let ((?x34 (bvmul ((_ zero_extend 3) ((_ extract 1 0) ((_ extract 7 0) a))) ((_ zero_extend 2) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) b)))))))
(let ((?x11 ((_ zero_extend 1) ((_ extract 4 0) ((_ zero_extend 3) ?x34)))))
(let (($x6 (and (distinct (ite (bvult a (_ bv4 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x65 (ite $x6 ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ zero_extend 2) (bvadd ?x11 ?x11))))) c)))
(let ((?x15 ((_ extract 7 0) (bvmul ((_ extract 7 0) a) ((_ zero_extend 5) ((_ extract 2 0) b))))))
(and (distinct (ite $x6 (bvadd ?x15 ?x15) c) ?x65) true)))))))
(check-sat)
